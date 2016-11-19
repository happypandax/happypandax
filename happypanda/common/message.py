"Contains classes/functions used to encapsulate message structures"

import enum
from lxml import etree
from lxml.builder import E

from happypanda.common import constants, exceptions
from happypanda.core import db

def finalize(xml):
    "Finalize XML message before sending"
    return etree.tostring(E.hp(xml, api=constants.version_api), encoding='utf-8')

def msg(cnt, type=str):
    "Compose a quick finalized XML message"
    m = CoreMessage.string
    if type is int:
        m = CoreMessage.int
    elif type == 'timestamp': ## probably confusing?
        m = CoreMessage.timestamp
    return finalize(m(cnt))

class CoreMessage:
    "Encapsulates return values from methods in the interface module"

    class MessageType(enum.Enum):
        Status = 1
        Gallery = 2

    def __init__(self, msg_type):
        self.type = msg_type

    def toXML(self):
        "Serialize to XML structure"
        raise NotImplementedError()

    def toString(self):
        "Serialize this object to XML string"
        return finalize(self.toXML())

    def fromXML(self, xml):
        raise NotImplementedError()

    def safe(self, txt):
        "Transform to appropriate characters"
        if txt is None:
            return ''
        else:
            return txt

    @staticmethod
    def string(c):
        "<string>"
        assert isinstance(c, str)
        return E.string(c)

    @staticmethod
    def int(c):
        "<int>"
        assert isinstance(c, int)
        return E.int(c)

    @staticmethod
    def timestamp(c):
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
                self.safe(self.error)
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

    @staticmethod
    def fromXML(xml):
        g = Gallery()
        return g


    def _unpackCollection(self, model_attrib, tag):
        "Helper method to unpack a SQLalchemy collection"
        return self.safe('')

    def _unpackAttrib(self, model_attrib):
        "Helper method to unpack a SQLalchemy attribute"
        return self.safe('')

