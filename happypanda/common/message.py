"Contains classes/functions used to encapsulate message structures"

import enum
import json

from datetime import datetime

from happypanda.common import constants, exceptions
from happypanda.server.core import db

def finalize(js):
    "Finalize json message before sending"
    enc = 'utf-8'
    wrap = {
        'name':constants.server_name,
        'version':[constants.version, str(constants.version_db[0])]}
    json_data = wrap['data'] = js

    return bytes(json.dumps(json_data), enc)

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
        "Implement in subclass. Must return a dict if intended to be serializable."
        raise NotImplementedError()

    def from_json(self, j):
        raise NotImplementedError()

    def serialize(self):
        "Serialize to JSON structure"
        d = self.data()
        assert isinstance(d, dict), "self.data() must return a dict!"
        if self._error:
            d[self._error.key] = self._error.data()
        return {self.key: d}

    def finalize(self):
        "Serialize this object to bytes"
        return finalize(self.serialize())

class List(CoreMessage):
    """
    Encapsulates a list of objects of the same type
    Note: You must use this in conjunction with other viable CoreMessage derivatives
    """

    def __init__(self, key, type_):
        super().__init__(key)
        self._type = type_
        self.items = []

    def append(self, item):
        assert isinstance(item, self._type), "item must be a {}".format(self._type)
        d = item.data() if isinstance(item, CoreMessage) else item
        self.items.append(d)

    def data(self):
        return self.items

    def from_json(self, j):
        return super().from_json(j)


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
        assert isinstance(msg, Message)
        self.error = error
        self.msg = msg

    def data(self):
        return {'code':self.error, self.msg.key:self.msg.data()}

    def from_json(self, j):
        return super().from_json(j)

class DatabaseMessage(CoreMessage):
    "Database item mapper"
    def __init__(self, key, db_item):
        super().__init__(key)
        assert isinstance(db_item, db.Base)
        assert db.is_instanced(db_item), "must be instanced database object"
        self.item = db_item

    def data(self, load_values=False, load_collections=False):
        """
        Params:
            load_values -- Queries database for unloaded values
            load_collections -- Queries database to fetch all items in a collection
        """
        self._check_link()
        gattribs = db.table_attribs(self.item, not load_values)
        return {x: self._unpack(gattribs[x], load_collections) for x in gattribs}

    def _unpack(self, attrib, load_collections):
        "Helper method to unpack SQLalchemy objects"
        if attrib is None:
            return

        # beware lots of recursion
        if db.is_instanced(attrib):
            msg_obj = None
            if isinstance(attrib, db.Gallery):
                msg_obj = Gallery(attrib)
            elif isinstance(attrib, db.Artist):
                msg_obj = Artist(attrib)
            else:
                raise NotImplementedError("Message encapsulation for this database object does not exist ({})".format(type(attrib)))

            return msg_obj.data() if msg_obj else None

        elif db.is_list(attrib) or isinstance(attrib, list):
            return [self._unpack(x, load_collections) for x in attrib]

        elif db.is_query(attrib):
            if load_collections:
                return [self._unpack(x, load_collections) for x in attrib.all()]
            else:
                return []

        elif isinstance(attrib, datetime):
            return attrib.timestamp()

        elif isinstance(attrib, (bool, int, str)):
            return attrib
        else:
            raise NotImplementedError("Unpacking method for this attribute does not exist ({})".format(type(attrib)))

    def _check_link(self):
        if not self.item:
            raise exceptions.CoreError("This object has no linked database item")

class Gallery(DatabaseMessage):
    "Encapsulates database gallery object"

    def __init__(self, db_gallery):
        assert isinstance(db_gallery, db.Gallery)
        super().__init__('gallery', db_gallery)

    def from_json(self, j):
        return super().from_json(j)

class Artist(DatabaseMessage):
    "Encapsulates database artist object"

    def __init__(self, db_gallery):
        assert isinstance(db_item, db.Artist)
        super().__init__('artist', db_item)

    def from_json(self, j):
        return super().from_json(j)

class Function(CoreMessage):
    "A function message"

    def __init__(self, fname, data = None):
        super().__init__('function')
        assert isinstance(fname, str)
        self.name = fname
        self._data = data

    def set_data(self, d):
        ""
        assert isinstance(d, CoreMessage)
        self._data = d

    def data(self):
        assert self._data, "No data set"
        return {'fname':self.name, 'data':self._data.data()}

    def from_json(self, j):
        return super().from_json(j)

