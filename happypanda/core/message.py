"Contains classes/functions used to encapsulate message structures"

import enum
import json
import inspect
import arrow
import os

from datetime import datetime

from happypanda.common import constants, exceptions, utils, hlogger, config
from happypanda.core import db
from happypanda.core.commands import io_cmd

log = hlogger.Logger(__name__)


def finalize(msg_dict, session_id="", name=None, error=None):
    "Finalize dict message before sending"
    enc = 'utf-8'
    msg = {
        'session': session_id,
        'name': name if name else config.server_name.value,
        'data': msg_dict,
    }

    if error:
        msg['error'] = error

    return bytes(json.dumps(msg), enc)


class CoreMessage:
    "Encapsulates return values from methods in the interface module"

    def __init__(self, key):
        self.key = key
        self._error = None

    def set_error(self, e):
        "Set an error message"
        assert isinstance(e, Error)
        self._error = e

    def data(self):
        "Implement in subclass. Must return a dict or list if intended to be serializable."
        raise NotImplementedError()

    def from_json(self, j):
        raise NotImplementedError()

    def json_friendly(self, include_key=True):
        "Serialize to JSON structure"
        d = self.data()
        assert isinstance(
            d, (dict, list)) or isinstance(self, Message), "self.data() must return a dict or list!"
        if self._error:
            d[self._error.key] = self._error.data()
        if include_key:
            return {self.key: d}
        else:
            return d

    def serialize(self, session_id="", name=None):
        "Serialize this object to bytes"
        return finalize(self.json_friendly(), session_id, name)


class Identity(CoreMessage):
    """
    Encapsulates any type of object
    """

    def __init__(self, key, obj=None):
        super().__init__(key)
        self._obj = obj

    def data(self):
        return self._obj

    def json_friendly(self, include_key=True):
        "Serialize to JSON structure"
        d = self.data()
        if include_key:
            return {self.key: d}
        else:
            return d


class List(CoreMessage):
    """
    Encapsulates a list of objects of the same type
    """

    def __init__(self, key, type_):
        super().__init__(key)
        self._type = type_
        self.items = []

    def append(self, item):
        assert isinstance(
            item, self._type), "item must be a {}".format(
            self._type)
        d = item.json_friendly(
            include_key=False) if isinstance(
            item, CoreMessage) else item
        self.items.append(d)

    def data(self):
        return self.items

    def from_json(self, j):
        return super().from_json(j)

    def serialize(self, session_id="", name=None, include_key=False):
        "Serialize this object to bytes"
        d = self.json_friendly(include_key)
        return finalize(d, session_id, name)


class Message(CoreMessage):
    "An arbitrary remark"

    def __init__(self, msg):
        super().__init__('msg')
        self.msg = msg

    def data(self):
        return self.msg

    def from_json(self, j):
        return super().from_json(j)


class Error(CoreMessage):
    "An error object"

    def __init__(self, error, msg):
        super().__init__('error')
        assert isinstance(msg, (Message, str))
        if isinstance(msg, str):
            msg = Message(msg)
        self.error = error
        self.msg = msg

    def data(self):
        return {'code': self.error, self.msg.key: self.msg.data()}

    def from_json(self, j):
        return super().from_json(j)


class DatabaseMessage(CoreMessage):
    "Database item mapper"

    _clsmembers = None  # not all classes have been defined yet
    _db_clsmembers = [
        x for x in inspect.getmembers(
            db, inspect.isclass) if issubclass(
            x[1], db.Base)]

    def __init__(self, key, db_item):
        super().__init__(key)
        assert isinstance(db_item, db.Base)
        assert db.is_instanced(db_item), "must be instanced database object"
        self.item = db_item
        DatabaseMessage._clsmembers = {
            x: globals()[x] for x in globals() if inspect.isclass(
                globals()[x])}

    def _before_data(self):
        self._check_link()
        db.ensure_in_session(self.item)

    def data(self, load_values=False, load_collections=False):
        """
        Params:
            load_values -- Queries database for unloaded values
            load_collections -- Queries database to fetch all items in a collection
        """
        self._before_data()
        gattribs = db.table_attribs(self.item, not load_values)
        return {
            x: self._unpack(
                x,
                gattribs[x],
                load_collections) for x in gattribs}

    def json_friendly(
            self,
            load_values=False,
            load_collections=False,
            include_key=True):
        """Serialize to JSON structure
        Params:
            load_values -- Queries database for unloaded values
            load_collections -- Queries database to fetch all items in a collection
        """
        if self.item:
            db.ensure_in_session(self.item)
        d = self.data(load_values, load_collections)
        assert isinstance(d, dict), "self.data() must return a dict!"
        if self._error:
            d[self._error.key] = self._error.data()
        if include_key:
            return {self.key: d}
        else:
            return d

    def serialize(
            self,
            session_id="",
            load_values=False,
            load_collections=False,
            name=None):
        """Serialize this object to bytes
                Params:
            load_values -- Queries database for unloaded values
            load_collections -- Queries database to fetch all items in a collection
        """
        return finalize(
            self.json_friendly(
                load_values,
                load_collections),
            session_id,
            name)

    def _unpack_metatags(self, attrib):
        m_tags = {x: False for x in db.MetaTag.all_names()}
        names = []
        if db.is_query(attrib):
            names = tuple(x.name for x in attrib.all())
        elif db.is_list(attrib) or isinstance(attrib, list):
            names = tuple(x.name for x in attrib)
        for n in names:
            m_tags[n] = True
        return m_tags

    def _unpack(self, name, attrib, load_collections):
        "Helper method to unpack SQLalchemy objects"
        if attrib is None:
            return

        if name == "metatags":
            return self._unpack_metatags(attrib)

        #log.d("name:", name, "attrib:", attrib)
        # beware lots of recursion
        if db.is_instanced(attrib):
            msg_obj = None

            exclude = (db.NameMixin.__name__,)

            for cls_name, cls_obj in self._db_clsmembers:
                if cls_name not in exclude:
                    if isinstance(attrib, cls_obj):
                        if cls_name in self._clsmembers:
                            msg_obj = self._clsmembers[cls_name](attrib)
                            break

            if not msg_obj:
                if isinstance(attrib, db.NameMixin):
                    msg_obj = NameMixin(attrib, name)
                else:
                    raise NotImplementedError(
                        "Message encapsulation for this database object does not exist ({})".format(
                            type(attrib)))

            return msg_obj.data() if msg_obj else None

        elif db.is_list(attrib) or isinstance(attrib, list):
            return [self._unpack(name, x, load_collections) for x in attrib]

        elif db.is_query(attrib):
            if load_collections:
                return [self._unpack(name, x, load_collections)
                        for x in attrib.all()]
            else:
                return []

        elif isinstance(attrib, enum.Enum):
            return attrib.name

        elif isinstance(attrib, datetime):
            return attrib.timestamp()

        elif isinstance(attrib, arrow.Arrow):
            return attrib.timestamp

        elif isinstance(attrib, (bool, int, float, str, dict)):
            return attrib
        else:
            raise NotImplementedError(
                "Unpacking method for this attribute does not exist ({})".format(
                    type(attrib)))

    def _check_link(self):
        if not self.item:
            raise exceptions.CoreError(
                "This object has no linked database item")


class Gallery(DatabaseMessage):
    "Encapsulates database gallery object"

    def __init__(self, db_gallery):
        assert isinstance(db_gallery, db.Gallery)
        super().__init__('gallery', db_gallery)

    def from_json(self, j):
        return super().from_json(j)


class Artist(DatabaseMessage):
    "Encapsulates database artist object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Artist)
        super().__init__('artist', db_item)

    def from_json(self, j):
        return super().from_json(j)


class Parody(DatabaseMessage):
    "Encapsulates database parody object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Parody)
        super().__init__('parody', db_item)

    def from_json(self, j):
        return super().from_json(j)


class Collection(DatabaseMessage):
    "Encapsulates database collection object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Collection)
        super().__init__('collection', db_item)


class Grouping(DatabaseMessage):
    "Encapsulates database grouping object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Grouping)
        super().__init__('grouping', db_item)


class Taggable(DatabaseMessage):
    "Encapsulates database taggable object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Taggable)
        super().__init__('taggable', db_item)


class NameMixin(DatabaseMessage):
    "Encapsulates database namemixin object"

    def __init__(self, db_item, name=""):
        assert isinstance(db_item, db.NameMixin)
        if not name:
            name = db_item.__tablename__
        super().__init__(name, db_item)

    def from_json(self, j):
        return super().from_json(j)


class NamespaceTags(DatabaseMessage):
    "Encapsulates database namespacetag object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.NamespaceTags)
        super().__init__('nstag', db_item)

    def data(self, load_values=False, load_collections=False):
        self._before_data()
        d = {}
        d[self.item.namespace.name] = Tag(self.item.tag, self).json_friendly(include_key=False)
        d[db.MetaTag.__tablename__] = self._unpack_metatags(self.item.metatags)
        return d


class Tag(DatabaseMessage):
    "Encapsulates database tag object"

    def __init__(self, db_item, nstag=None):
        assert isinstance(db_item, db.Tag)
        super().__init__('tag', db_item)
        self.nstag = nstag

    def data(self, load_values=False, load_collections=False):
        self._before_data()
        d = {}
        aliases = []
        d['name'] = self.item.name
        if self.nstag:
            for a in self.nstag.aliases:
                aliases.appned(a.tag.name)
        d['aliases'] = aliases
        return d


class Profile(DatabaseMessage):
    "Encapsulates database profile object"

    def __init__(self, db_item, url=True, uri=False):
        assert isinstance(db_item, db.Profile)
        super().__init__('profile', db_item)
        self._local_url = url
        self._uri = uri

    def data(self, load_values=False, load_collections=False):
        self._before_data()
        d = {}
        path = io_cmd.CoreFS(self.item.path)
        d['id'] = self.item.id
        if path.ext == constants.link_ext:
            d['ext'] = io_cmd.CoreFS(self.item.path[:-len(path.ext)]).ext
        else:
            d['ext'] = path.ext
        if self._local_url:
            _, tail = os.path.split(path.get())
            # TODO: make sure path is in static else return actual path
            if tail:
                furl = constants.thumbs_view + '/' + tail
                d['data'] = furl
            else:
                d['data'] = ""
        else:
            im = ""
            if path.exists:
                with path.open("rb") as f:
                    im = utils.imagetobase64(f.read())
            if self._uri:
                im = im.replace('\n', '')
                im = "data:image/{};base64,".format(path.ext[1:]) + im
            d['data'] = im
        d['size'] = self.item.size
        d['timestamp'] = self.item.timestamp.timestamp if self.item.timestamp else None
        return d

    def from_json(self, j):
        return super().from_json(j)


class Page(DatabaseMessage):
    "Encapsulates database page object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Page)
        super().__init__('page', db_item)

    def from_json(self, j):
        return super().from_json(j)


class Title(DatabaseMessage):
    "Encapsulates database title object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Title)
        super().__init__('title', db_item)

    def from_json(self, j):
        return super().from_json(j)


class Url(DatabaseMessage):
    "Encapsulates database url object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.Url)
        super().__init__('url', db_item)

    def from_json(self, j):
        return super().from_json(j)


class GalleryFilter(DatabaseMessage):
    "Encapsulates database galleryfilter object"

    def __init__(self, db_item):
        assert isinstance(db_item, db.GalleryFilter)
        super().__init__('galleryfilter', db_item)

    def from_json(self, j):
        return super().from_json(j)


class Function(CoreMessage):
    "A function message"

    def __init__(self, fname, data=None, error=None):
        super().__init__('function')
        assert isinstance(fname, str)
        self.name = fname
        self.set_data(data)
        if error:
            self.set_error(error)

    def set_data(self, d):
        ""
        assert isinstance(d, CoreMessage) or d is None
        self._data = d

    def data(self):
        d = self._data.json_friendly(include_key=False) if self._data else None
        return {'fname': self.name, 'data': d}

    def from_json(self, j):
        return super().from_json(j)
