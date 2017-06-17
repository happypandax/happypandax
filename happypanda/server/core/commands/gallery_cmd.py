from happypanda.common import utils, hlogger
from happypanda.server.core.command import Command, UndoCommand, CommandEvent, CommandEntry
from happypanda.server.core import db
from happypanda.server.interface import enums


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

    @rename.default
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


class FilterGallery(Command):
    """
    Returns filtered galleries
    """

    set_search_filter = CommandEntry("set_search_filter", str, str)
    search_filter = CommandEvent("search_filter", str)

    parse_search_filter = CommandEntry("parse_search_filter",)

    def __init__(self):
        super().__init__()
        self._search = ''
        self._filter_id = None
        self._view_type = None

    @set_search_filter.default
    def _set_s_filter(s_filter):
        return s_filter

    def _parse_search(self, search_filter):
        ""
        #ops = []

    def main(self, search_filter: str, gallery_filter_id: int=None,
             view_type: enums.ViewType=None) -> None:

        with self.set_search_filter(search_filter) as plg:
            self._search = plg.first()

        self.search_filter.emit(self._search)

        self._parse_operators(search_filter)
