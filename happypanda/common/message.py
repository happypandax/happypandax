"Contains classes/functions used to encapsulate message structures"

import enum
import json

from happypanda.common import constants, exceptions
from happypanda.server.core import db

def finalize(js):
    "Finalize json message before sending"
    json_string = b''
    enc = 'utf-8'
    wrap = {'name':constants.version}
    json_string = wrap['data'] = js

    return bytes(json.dumps(json_string), enc)

def msg(cnt):
    """Compose a quick finalized json message."""
    assert not isinstance(cnt, (dict, list, tuple))
    return finalize({'msg':cnt})

def server_info():
    "Serializes server, api and database versions"
    m = {
        'version':[constants.version, str(constants.version_db[0])],
        }
    return finalize(m)

class CoreMessage:
    "Encapsulates return values from methods in the interface module"

    def __init__(self, key):
        self.key = key

    def data(self):
        raise NotImplementedError()

    def from_json(self, j):
        raise NotImplementedError()

    def to_json(self):
        "Serialize to JSON structure"
        return {self.key:self.data()}

    def finalize(self):
        "Serialize this object to bytes"
        return finalize(self.to_json())


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

class Gallery(CoreMessage):
    "A gallery object"

    def __init__(self, db_gallery):
        super().__init__('gallery')
        assert isinstance(db_gallery, db.Gallery)
        self.db_gallery = db_gallery

    def data(self):
        self._check_link()
        return {
            'id':self.db_gallery.id,
            'title':self._unpack_collection(self.db_gallery.titles),
            'author':self._unpack_collection(self.db_gallery.artists),
            'circle':self._unpack_collection(self.db_gallery.circles),
            'language':self._unpack_attrib(self.db_gallery.language),
            'type':self._unpack_attrib(self.db_gallery.type),
            'path':self.db_gallery.path,
            'archive_path':self.db_gallery.path_in_archive,
            }

    def to_json(self):
        self._check_link()
        return super().to_json()

    def from_json(self, j):
        return super().from_json(j)

    def _unpack_collection(self, model_attrib):
        "Helper method to unpack a SQLalchemy collection"
        return

    def _unpack_attrib(self, model_attrib):
        "Helper method to unpack a foreign SQLalchemy attribute"
        return

    def _check_link(self):
        if not self.db_gallery:
            raise exceptions.CoreError("This object has no linked database gallery")

