"Contains classes/functions used to encapsulate message structures"

import enum
import json

from happypanda.common import constants, exceptions
from happypanda.server.core import db

def finalize(js):
    "Finalize json message before sending"
    json_string = b''
    enc = 'utf-8'
    wrap = {'api':constants.version_api}
    json_string = wrap['data'] = js

    return bytes(json.dumps(json_string), enc)

def msg(cnt):
    """Compose a quick finalized json message."""
    assert not isinstance(cnt, (dict, list, tuple))
    return finalize({'msg':cnt})

def serverInfo():
    "Serializes server, api and database versions"
    m = {
        'version':[constants.version, str(constants.version_db[0])],
        }
    return finalize(m)


class CoreMessage:
    "Encapsulates return values from methods in the interface module"

    class MessageType(enum.Enum):
        Status = 1
        Gallery = 2

    def __init__(self, msg_type):
        self.type = msg_type

    def toJSON(self):
        "Serialize to JSON structure"
        raise NotImplementedError()

    def finalize(self):
        "Serialize this object to bytes"
        return finalize(self.toJSON())

    def fromJSON(self, j):
        raise NotImplementedError()

class Status(CoreMessage):
    ""

    def __init__(self, error):
        super().__init__(CoreMessage.MessageType.Status)
        self.error = error

    def toJSON(self):
        return {'error':self.error}

    def fromJSON(self, j):
        return super().fromJSON(j)

class Gallery(CoreMessage):
    ""

    def __init__(self):
        super().__init__(CoreMessage.MessageType.Gallery)
        self.db_gallery = []

    def add(self, other):
        ""
        assert isinstance(other, (Gallery, db.Gallery))
        if isinstance(other, Gallery):
            self.db_gallery.extend(other.db_gallery)
        else:
            self.db_gallery.append(other)

    def toJSON(self):
        if not self.db_gallery:
            raise exceptions.CoreError("This object has no galleries")
        j = {'gallery':[self.unpackGallery(x) for x in self.db_gallery]}
        return j

    @staticmethod
    def fromJSON(self, j):
        g = Gallery()
        return g

    def unpackGallery(self, db_gallery):
        "Helper method to unpack a db.Gallery"
        assert isinstance(db_gallery, db.Gallery)
        g = {
            'id':db_gallery.id,
            'title':self._unpackCollection(self.db_gallery.titles),
            'author':self._unpackCollection(self.db_gallery.artists),
            'circle':self._unpackCollection(self.db_gallery.circles),
            'language':self._unpackAttrib(self.db_gallery.language),
            'type':self._unpackAttrib(self.db_gallery.type),
            'path':db_gallery.path,
            'archive_path':db_gallery.path_in_archive,
            }
        return g

    def _unpackCollection(self, model_attrib):
        "Helper method to unpack a SQLalchemy collection"
        return

    def _unpackAttrib(self, model_attrib):
        "Helper method to unpack a foreign SQLalchemy attribute"
        return

