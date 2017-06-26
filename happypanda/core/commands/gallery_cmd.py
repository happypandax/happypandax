from happypanda.common import utils, hlogger
from happypanda.core.command import UndoCommand, CommandEvent, CommandEntry
from happypanda.core import db

log = hlogger.Logger(__name__)


class RenameGallery(UndoCommand):
    """
    Rename a gallery
    """

    renamed = CommandEvent("renamed", str)
    rename = CommandEntry("rename", None, str, str)

    def __init__(self):
        super().__init__()
        self.title = None
        self.old_title = None

    @rename.default()
    def _set_title(old_title, new_title):
        return new_title

    def main(self, title: db.Title, new_title: str) -> None:

        self.title = title
        self.old_title = title.name

        with self.rename.call(title.name, new_title) as plg:
            title.name = plg.first()

            with utils.session() as s:
                s.add(title)

        self.renamed.emit(title.name)

    def undo(self):
        self.title.name = self.old_title

        with utils.session() as s:
            s.add(self.title)

        self.renamed.emit(self.old_title)


class AddGallery(UndoCommand):
    """
    Add a gallery
    """

    added = CommandEvent("added", db.Gallery)

    def __init__(self):
        super().__init__()

    def main(self, gallery: db.Gallery) -> None:
        pass

    def undo(self):
        return super().undo()
