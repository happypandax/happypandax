"Contains classes used to encapsulate message structures"

import enum
from lxml import etree
from lxml.builder import E

from happypanda.common import constants, exceptions
from happypanda.core import db

class CoreMessage:
    "Encapsulates return values from methods in the interface module"

    class MessageType(enum.Enum):
        Status = 1
        Gallery = 2

    def __init__(self, msg_type):
        self.type = msg_type

    def toXML(self):
        "Convert to XML structure"
        raise NotImplementedError()
        

    def toString(self):
        return etree.tostring(E.hp(self.toXML(), api=constants.version_api), encoding='utf-8')

    def fromXML(self, xml):
        raise NotImplementedError()

    def safe(self, txt):
        "Transform to appropriate characters"
        if txt is None:
            return ''
        else:
            return txt

    def string(self, c):
        "<string>"
        assert isinstance(c, str)
        return E.string(c)

    def int(self, c):
        "<int>"
        assert isinstance(c, int)
        return E.int(c)

    def timestamp(self, c):
        "<timestamp>"
        assert isinstance(c, float)
        return E.timestamp(c)


class Status(CoreMessage):
    ""

    def __init__(self, error):
        super().__init__(CoreMessage.MessageType.Status)
        self.error = error

    def toXML(self):
        xml = E.status(
            E.error(
                self.error
                )
            )
        return xml

    def fromXML(self, xml):
        return super().fromXML()

class Gallery(CoreMessage):
    ""

    def __init__(self):
        super().__init__(CoreMessage.MessageType.Gallery)
        self.db_gallery = None

    def toXML(self):
        if not self.db_gallery:
            raise exceptions.CoreError("No gallery has been linked")
        assert isinstance(self.db_gallery, db.Gallery)
        xml = E.gallery(
                E.id(self.int(self.safe(self.db_gallery.path))),
                E.title(*self._unpackCollection(self.db_gallery.titles, "string")),
                E.author(*self._unpackCollection(self.db_gallery.artists, "string")),
                E.circle(*self._unpackCollection(self.db_gallery.circles, "string")),
                E.language(*self._unpackAttrib(self.db_gallery.language)),
                E.type(*self._unpackAttrib(self.db_gallery.type)),
                E.path(self.safe(self.db_gallery.path)),
                E.path_in_archive(self.safe(self.db_gallery.path_in_archive)),
                )
        return xml


    def fromXML(self, xml):
        return super().fromXML()

    def _unpackCollection(self, model_attrib, tag):
        "Helper method to unpack a SQLalchemy collection"
        return self.safe('')

    def _unpackAttrib(self, model_attrib):
        "Helper method to unpack a SQLalchemy attribute"
        return self.safe('')

