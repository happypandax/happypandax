from happypanda.common import utils, hlogger
from happypanda.server.core.command import Command, UndoCommand, CommandEvent, CommandEntry
from happypanda.server.core import db


log = hlogger.Logger(__name__)

class GalleryRename(UndoCommand):
    """
    Rename a gallery
    """

    renamed = CommandEvent("renamed")
    rename = CommandEntry("rename", None)

    def __init__(self):
        super().__init__()
        self.gallery = None
        self.title = None
        self.old_title = None

    def main(self, gallery: db.Gallery, title: db.Title, new_title: str) -> None:

        self.gallery = gallery
        self.title = title
        self.old_title = title.name

        with utils.session() as s:
            title.name = new_title
            s.add(title)

        self._renamed.emit(title.name)
            
    def undo(self):
        self.title.name = self.old_title

        with utils.session() as s:
            s.add(self.title)

        self._renamed.emit(self.old_title)

