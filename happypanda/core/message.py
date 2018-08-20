"Contains classes/functions used to encapsulate message structures"

import enum
import inspect
import arrow
import os
import itertools
import multidict

from datetime import datetime

from happypanda.common import constants, exceptions, utils, hlogger, config
from happypanda.core import db, plugins
from happypanda.core.commands import io_cmd

log = hlogger.Logger(constants.log_ns_server + __name__)


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

    return bytes(utils.json_dumps(msg), enc)


class CoreMessage:
    "Encapsulates return values from methods in the interface module"

    def __init__(self, key):
        self.key = key
        self._error = None

    def set_error(self, e):
        "Set an error message"
        assert isinstance(e, Error)
        self._error = e

    def _incompatible_type(self, x):
        if not isinstance(x, (dict, str, int, float, list)):
            raise ValueError("Incompatible type: {}".format(type(x)))

    def data(self, **kwargs):
        "Implement in subclass. Must return a dict or list if intended to be serializable."
        raise NotImplementedError()

    @classmethod
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


class Notification(CoreMessage):
    """
    """
    _id_counter = itertools.count(constants.PushID.User.value)

    def __init__(self, msg, title="", *actions):
        super().__init__("notification")
        self.id = next(self._id_counter)
        self.title = title
        self.msg = msg
        self.actions = list(actions)
        self.expired = False

    def add_action(self, actionid, text, actiontype):
        self.actions.append({
            'id': actionid,
            'text': text,
            'type': actiontype})

    def data(self, **kwargs):
        d = {
            'id': self.id,
            'title': self.title,
            'body': self.msg,
            'expired': self.expired,
        }

        if self.actions:
            d['actions'] = self.actions

        return d


class Identity(CoreMessage):
    """
    Encapsulates any type of object
    """

    def __init__(self, key, obj=None):
        super().__init__(key)
        self._obj = obj

    def data(self, **kwargs):
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
        self._incompatible_type(d)
        self.items.append(d)

    def data(self, **kwargs):
        return self.items

    def serialize(self, session_id="", name=None, include_key=False):
        "Serialize this object to bytes"
        d = self.json_friendly(include_key)
        return finalize(d, session_id, name)


class Message(CoreMessage):
    "An arbitrary remark"

    def __init__(self, msg):
        super().__init__('msg')
        self.msg = msg

    def data(self, **kwargs):
        return self.msg


class Error(CoreMessage):
    "An error object"

    def __init__(self, error, msg):
        super().__init__('error')
        assert isinstance(msg, (Message, str))
        if isinstance(msg, str):
            msg = Message(msg)
        self.error = error
        self.msg = msg

    def data(self, **kwargs):
        return {'code': self.error, self.msg.key: self.msg.data()}


class DatabaseMessage(CoreMessage):
    "Database item mapper"

    class NoUnpack(Exception):
        pass

    _msg_path = []
    _clsmembers = None  # not all classes have been defined yet
    _db_clsmembers = [
        x for x in inspect.getmembers(
            db, inspect.isclass) if issubclass(
            x[1], db.Base)]

    db_type = None

    def __init__(self, key, db_item):
        super().__init__(key)
        assert db.is_instanced(db_item), f"must be instanced database object not '{db_item}'"
        assert isinstance(db_item, self.db_type) if self.db_type else isinstance(
            db_item, db.Base), f"a {self.db_type} is required not '{type(db_item)}'"
        self.item = db_item
        self._recursive_depth = 2
        self._indirect = False
        self._msg_path = []
        self._sess = None
        self._detached = db.is_detached(db_item)
        self._properties = self.properties()
        DatabaseMessage._clsmembers = {
            x: globals()[x] for x in globals() if inspect.isclass(
                globals()[x])}

    def properties(self):
        return {'exclusions': multidict.MultiDict(),
                'force_value_load': {}}

    def exclude_attributes(self, exclusions=tuple()):
        self.exclusions = exclusions
        self._properties['exclusions'].update(self._dict_tree_unpack(exclusions, multidict.MultiDict()))

    def _dict_tree_unpack(self, t, d=None):
        """
        a.b.c -> {'a': {'b': {'c': {}}}}
        """
        if d is None:
            d = {}
        for x in t:
            v = d
            for k in x.split('.'):
                if isinstance(v, multidict.MultiDict) and len(v.getall(k, [])) > 1:
                    a = v.getall(k)
                    for a_v in a:
                        if a_v:
                            v = a_v
                            break
                    else:
                        v = v.getone(k)
                else:
                    v = v.setdefault(k, {})
        return d

    def _before_data(self):
        self._check_link()
        if not self._detached and self.item and self.item.id:
            db.ensure_in_session(self.item)
        self._sess = db.object_session(self.item)
        self._msg_path.append(self.__class__.__name__)

    def data(self, load_values=False, load_collections=False,
             bypass_exclusions=False, propagate_bypass=False,
             force_value_load=None):
        """
        Params:
            load_values -- Queries database for unloaded values
            load_collections -- Queries database to fetch all items in a collection
        """
        self._before_data()
        if force_value_load is not None:
            self._properties['force_value_load'] = self._dict_tree_unpack(force_value_load)

        with db.no_autoflush(self._sess):
            ex = tuple(x for x, y in self._properties['exclusions'].items() if not y)
            default_ex = ('user',)
            gattribs = db.table_attribs(self.item, not load_values, descriptors=True, raise_err=not self._detached,
                                        exclude=ex + default_ex if not bypass_exclusions else default_ex,
                                        allow=tuple(self._properties['force_value_load'].keys()))
            for i in ('_properties',):
                gattribs.pop(i, False)

            r = {}
            for x, v in gattribs.items():
                try:
                    r[x] = self._unpack(x, v, load_values, load_collections, propagate_bypass)
                except DatabaseMessage.NoUnpack:
                    pass
        return r

    def json_friendly(
            self,
            load_values=False,
            load_collections=False,
            include_key=True,
            bypass_exclusions=False,
            propagate_bypass=False,
            force_value_load=None):
        """Serialize to JSON structure
        Params:
            load_values -- Queries database for unloaded values
            load_collections -- Queries database to fetch all items in a collection
        """
        d = self.data(load_values, load_collections,
                      bypass_exclusions=bypass_exclusions,
                      propagate_bypass=propagate_bypass,
                      force_value_load=force_value_load)
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

    @classmethod
    def from_json(cls, msg, ignore_empty=True, skip_updating_existing=True,
                  skip_descriptors=False, _type=None,
                  ignore_private=True, _from_attr=''):
        db_obj = None
        if not msg:
            return db_obj

        if not isinstance(msg, dict):
            raise exceptions.InvalidMessage(
                utils.this_function(),
                f"Expected message object on '{_from_attr}' not '{type(msg).__name__}'")

        with db.no_autoflush(constants.db_session()) as sess:
            if not cls.db_type and _type is None:
                raise ValueError("A database type has not been set")
            db_type = _type or cls.db_type
            item_attrs = db.table_attribs(db_type, id=None, descriptors=True)

            if msg and not all((k in item_attrs.keys() for k in msg.keys())):
                m_keys = set(msg.keys()).difference(set(item_attrs.keys()))
                raise exceptions.InvalidMessage(
                    utils.this_function(),
                    f"Message object mismatch. '{_from_attr}' contains keys that are not present in the corresponding database item: {m_keys}")

            if msg:
                new_obj = True
                obj_id = msg.get('id', False)
                if obj_id:
                    db_obj = sess.query(db_type).get(obj_id)
                    if not db_obj:
                        raise exceptions.CoreError(utils.this_function(),
                                                   f"Existing item from message object with id '{obj_id}' was not found")
                    new_obj = False
                else:
                    db_obj = db_type()

                if new_obj and isinstance(db_obj, db.UniqueMixin):
                    if isinstance(db_obj, db.NameMixin) and msg.get('name') is not None:
                        db_obj = db_type.as_unique(name=msg.get('name'))
                        new_obj = bool(db_obj.id)
                    elif isinstance(db_obj, db.NamespaceTags):
                        ns_name = None
                        tag_name = None
                        try:
                            ns_name = utils.get_dict_value('namespace.name', msg)
                            tag_name = utils.get_dict_value('tag.name', msg)
                        except KeyError:
                            pass
                        if ns_name is not None and tag_name is not None:
                            db_obj = db_type.as_unique(ns=ns_name, tag=tag_name)
                            new_obj = bool(db_obj.id)
                    elif isinstance(db_obj, (db.Artist, db.Parody)):
                        a_names = set()
                        if msg.get('preferred_name') and msg['preferred_name'].get('name') is not None:
                            a_names.add(msg['preferred_name']['name'])
                        if msg.get('names'):
                            for n in msg['names']:
                                if n.get('name') is not None:
                                    a_names.add(n['name'])
                        if a_names:
                            db_obj = db_type.as_unique(names=a_names)
                            new_obj = bool(db_obj.id)

                if db_obj and not (obj_id and db_obj and skip_updating_existing):
                    for attr, value in msg.items():
                        if attr == 'id':
                            continue
                        if ignore_private and attr.startswith('_'):
                            continue
                        if ignore_empty:
                            if value is None:
                                continue
                            elif isinstance(value, (list, dict)) and not value:
                                continue

                        cls_attr = item_attrs[attr]
                        if skip_descriptors and db.is_descriptor(cls_attr):
                            continue
                        obj_attr = getattr(db_obj, attr) # noqa: F841
                        try:
                            col_model = db.column_model(cls_attr)
                        except TypeError:  # most likely a hybrid_property descriptor
                            col_model = None
                        if not issubclass(col_model, db.Base) if inspect.isclass(
                                col_model) else not isinstance(col_model, db.Base):
                            if isinstance(col_model, (db.Boolean, db.Integer, db.Password,
                                                      db.String, db.Text, db.LowerCaseString,
                                                      db.CapitalizedString)):
                                setattr(db_obj, attr, value)
                            elif isinstance(col_model, db.ArrowType):
                                setattr(db_obj, attr, arrow.Arrow.fromtimestamp(value))
                            elif db.is_descriptor(cls_attr):
                                if db.descriptor_has_setter(cls_attr):
                                    raise NotImplementedError
                            else:
                                raise NotImplementedError(
                                    f"Value deserializing for this database type does not exist ({col_model})")
                            continue

                        msg_obj = cls._get_message_object(cls, attr, col_model, check_recursive=False, class_type=True)
                        if col_model == db.Taggable and isinstance(value, dict):
                            if db_obj.taggable and db_obj.taggable.id:
                                value['id'] = db_obj.taggable.id
                        if issubclass(col_model, db.MetaTag):
                            setattr(db_obj, attr, msg_obj._pack_metatags(value))
                        elif db.is_list(cls_attr) or db.is_query(cls_attr):
                            n_l = []
                            for v in value:
                                o = msg_obj.from_json(
                                    v,
                                    _type=col_model,
                                    ignore_empty=ignore_empty,
                                    skip_updating_existing=skip_updating_existing,
                                    skip_descriptors=skip_descriptors,
                                    _from_attr=_from_attr + '.' + attr if _from_attr else attr,
                                )
                                if o is not None:
                                    n_l.append(o)
                            setattr(db_obj, attr, n_l)
                        elif db.is_descriptor(cls_attr):
                            if db.descriptor_has_setter(cls_attr):
                                raise NotImplementedError
                        else:
                            setattr(
                                db_obj,
                                attr,
                                msg_obj.from_json(
                                    value,
                                    _type=col_model,
                                    _from_attr=_from_attr + '.' + attr if _from_attr else attr,
                                    ignore_empty=ignore_empty,
                                    skip_updating_existing=skip_updating_existing,
                                    skip_descriptors=skip_descriptors))

        return db_obj

    @classmethod
    def _pack_metatags(cls, msg_obj):
        assert isinstance(msg_obj, dict)
        m_tags = []
        for k, v in msg_obj.items():
            if v:
                m_tags.append(db.MetaTag.as_unique(name=k))
        return m_tags

    @classmethod
    def _unpack_metatags(cls, attrib):
        m_tags = {x: False for x in db.MetaTag.all_names()}
        names = []
        if db.is_query(attrib):
            names = tuple(x.name for x in attrib.all())
        elif db.is_list(attrib) or isinstance(attrib, list):
            names = tuple(x.name for x in attrib)
        for n in names:
            m_tags[n] = True
        return m_tags

    @staticmethod
    def _get_message_object(self, name, attrib, check_recursive=True, class_type=False):
        msg_obj = None

        check_true = issubclass if class_type else isinstance

        if check_recursive and self.__class__.__name__ in self._msg_path:
            if self._recursive_depth <= len([x for x in self._msg_path if x == self.__class__.__name__]):
                return False

        exclude = (db.NameMixin.__name__,)

        for cls_name, cls_obj in self._db_clsmembers:
            if cls_name not in exclude:
                if check_true(attrib, cls_obj):
                    if cls_name in self._clsmembers:
                        msg_obj = self._clsmembers[cls_name] if class_type else self._clsmembers[cls_name](attrib)
                        break

        if not msg_obj:
            if check_true(attrib, db.NameMixin):
                msg_obj = NameMixin if class_type else NameMixin(attrib, name)
            else:
                raise NotImplementedError(
                    "Message encapsulation for this database object does not exist ({})".format(
                        attrib if class_type else type(attrib)))
        return msg_obj

    def _unpack(self, name, attrib, load_values, load_collections, propagate_bypass):
        "Helper method to unpack SQLalchemy objects"
        if attrib is None:
            return

        if name == "metatags":
            return self._unpack_metatags(attrib)

        #log.d("name:", name, "attrib:", attrib)
        # beware lots of recursion
        if db.is_instanced(attrib):
            msg_obj = self._get_message_object(self, name, attrib)
            if msg_obj is False:  # recursive checked
                return None

            msg_obj._indirect = True
            msg_obj._properties['force_value_load'] = utils.dict_merge(
                msg_obj._properties['force_value_load'], self._properties['force_value_load'].get(name, {}))
            msg_obj._properties['exclusions'] = self._properties['exclusions'].get(name, {})
            if self._detached:
                msg_obj._detached = self._detached
            msg_obj._msg_path = self._msg_path.copy()
            # note: don't pass load_collections here. use the force_value_load param
            return msg_obj.data(load_values=load_values, bypass_exclusions=propagate_bypass,
                                propagate_bypass=propagate_bypass) if msg_obj else None

        elif db.is_list(attrib) or isinstance(attrib, list):
            return [self._unpack(name, x, load_values, load_collections, propagate_bypass) for x in attrib]

        elif db.is_query(attrib):
            can_load = False
            if name in self._properties['force_value_load']:
                can_load = True
            if can_load or (load_collections and not self._detached):
                return [self._unpack(name, x, load_values, load_collections, propagate_bypass)
                        for x in attrib.all()]
            else:
                raise DatabaseMessage.NoUnpack

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

    db_type = db.Gallery

    def __init__(self, db_gallery):
        super().__init__('gallery', db_gallery)
        self.exclude_attributes(("first_page",
                                 "pages.gallery",
                                 "titles.gallery",
                                 "preferred_title.gallery"
                                 ))

    @classmethod
    def from_json(cls, msg, ignore_empty=True, skip_updating_existing=True, skip_descriptors=False, **kwargs):
        pref_title = msg.pop('preferred_title', False)
        obj = super().from_json(msg, ignore_empty, skip_updating_existing, skip_descriptors, **kwargs)
        with db.no_autoflush(db.object_session(obj) or constants.db_session()):
            if not skip_descriptors and pref_title:
                for mt in msg.get('titles', []):
                    if utils.compare_json_dicts(mt, pref_title):
                        break
                else:
                    t = Title.from_json(pref_title, ignore_empty=ignore_empty, skip_updating_existing=skip_updating_existing,
                                        skip_descriptors=skip_descriptors, **kwargs)
                    setattr(obj, 'preferred_title', t)

            if msg.get('pages'):
                obj.pages.reorder()
            if (msg.get('grouping') or msg.get('grouping_id')) and obj.grouping:
                obj.grouping.galleries.reorder()
        return obj


class Artist(DatabaseMessage):
    "Encapsulates database artist object"

    db_type = db.Artist

    def __init__(self, db_item):
        super().__init__('artist', db_item)


class Parody(DatabaseMessage):
    "Encapsulates database parody object"

    db_type = db.Parody

    def __init__(self, db_item):
        super().__init__('parody', db_item)


class Collection(DatabaseMessage):
    "Encapsulates database collection object"

    db_type = db.Collection

    def __init__(self, db_item):
        super().__init__('collection', db_item)


class Grouping(DatabaseMessage):
    "Encapsulates database grouping object"

    db_type = db.Grouping

    def __init__(self, db_item):
        super().__init__('grouping', db_item)

    @classmethod
    def from_json(cls, msg, ignore_empty=True, skip_updating_existing=True, skip_descriptors=False, **kwargs):
        obj = super().from_json(msg, ignore_empty, skip_updating_existing, skip_descriptors, **kwargs)
        with db.no_autoflush(db.object_session(obj) or constants.db_session()):
            if msg.get('galleries'):
                obj.galleries.reorder()
        return obj


class Taggable(DatabaseMessage):
    "Encapsulates database taggable object"

    db_type = db.Taggable

    def __init__(self, db_item):
        super().__init__('taggable', db_item)
        self.exclude_attributes(("tags",))


class NameMixin(DatabaseMessage):
    "Encapsulates database namemixin object"

    db_type = db.NameMixin

    def __init__(self, db_item, name=""):
        if not name:
            name = db_item.__tablename__
        super().__init__(name, db_item)
        self.db_type = type(db_item)


class NamespaceTags(DatabaseMessage):
    "Encapsulates database namespacetag object"

    db_type = db.NamespaceTags

    def __init__(self, db_item):
        super().__init__('nstag', db_item)

    def properties(self):
        d = super().properties()
        d['force_value_load'] = self._dict_tree_unpack(('tag', "namespace"))
        return d


class Tag(DatabaseMessage):
    "Encapsulates database tag object"

    db_type = db.Tag

    def __init__(self, db_item, nstag=None):
        assert isinstance(db_item, db.Tag)
        assert isinstance(nstag, db.NamespaceTags) or nstag is None
        super().__init__('tag', db_item)
        self.nstag = nstag

    def data(self, *args, **kwargs):
        d = super().data(*args, **kwargs)
        if self.nstag:
            d['id'] = self.nstag.id
        return d


class Namespace(DatabaseMessage):
    "Encapsulates database tag object"

    db_type = db.Namespace

    def __init__(self, db_item, nstag=None):
        assert isinstance(db_item, db.Namespace)
        assert isinstance(nstag, db.NamespaceTags) or nstag is None
        super().__init__('namespace', db_item)
        self.nstag = nstag


class Profile(DatabaseMessage):
    "Encapsulates database profile object"

    db_type = db.Profile

    def __init__(self, db_item, url=True, uri=False):
        super().__init__('profile', db_item)
        self._local_url = url
        self._uri = uri

    def data(self, load_values=False, load_collections=False, **kwargs):
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
            path = utils.get_real_file(path)
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


class Page(DatabaseMessage):
    "Encapsulates database page object"

    db_type = db.Page

    def __init__(self, db_item):
        super().__init__('page', db_item)


class Title(DatabaseMessage):
    "Encapsulates database title object"

    db_type = db.Title

    def __init__(self, db_item):
        super().__init__('title', db_item)

    def properties(self):
        d = super().properties()
        d['force_value_load'] = self._dict_tree_unpack(('language',))
        return d


class Url(DatabaseMessage):
    "Encapsulates database url object"

    db_type = db.Url

    def __init__(self, db_item):
        super().__init__('url', db_item)


class GalleryFilter(DatabaseMessage):
    "Encapsulates database galleryfilter object"

    db_type = db.GalleryFilter

    def __init__(self, db_item):
        super().__init__('galleryfilter', db_item)


class Circle(DatabaseMessage):
    "Encapsulates database circle object"

    db_type = db.Circle

    def __init__(self, db_item):
        super().__init__('circle', db_item)


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

    def data(self, **kwargs):
        d = self._data.json_friendly(include_key=False, **kwargs) if self._data else None
        return {'fname': self.name, 'data': d}


class Plugin(CoreMessage):
    "A plugin message"

    def __init__(self, node):
        super().__init__('plugin')
        assert isinstance(node, plugins.PluginNode)
        self.node = node

    def _node_data(self, node):
        return {'id': node.info.id,
                'name': node.info.name,
                'shortname': node.info.shortname,
                'version': node.info.version.public,
                'author': node.info.author,
                'description': node.info.description,
                'website': node.info.get('website', ''),
                'state': node.state.value,
                'status': node.status
                }

    def data(self, **kwargs):
        d = self._node_data(self.node)
        d['require'] = [self._node_data(x) for x in self.node.dependencies]
        return d


class GalleryFS(CoreMessage):
    ""

    def __init__(self, gfs, **kwargs):
        super().__init__('galleryfs')
        assert isinstance(gfs, io_cmd.GalleryFS)
        self._gfs = gfs
        self._kwargs = kwargs

    def data(self, **kwargs):
        g = Gallery(self._gfs.gallery).data(load_values=self._kwargs.get('load_values', True),
                                            load_collections=self._kwargs.get('load_collections', False),
                                            propagate_bypass=self._kwargs.get('propagate_bypass', False),
                                            force_value_load=("taggable.tags",
                                                              "pages",
                                                              "collections",))
        d = {'sources': self._gfs.get_sources(),
             'page_count': len(self._gfs.pages),
             'metadata_from_file': self._gfs.metadata_from_file,
             'exists': self._gfs.exists,
             'gallery': g}
        return d
