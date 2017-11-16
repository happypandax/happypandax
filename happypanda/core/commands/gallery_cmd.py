import pathlib
import os
import sys
import subprocess

from happypanda.common import utils, hlogger, config
from happypanda.core.command import (UndoCommand, CommandEvent,
                                     CommandEntry, Command)
from happypanda.core.commands import database_cmd
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

class OpenGallery(Command):
    """
    Open a gallery in an external viewer
    """

    _opened = CommandEvent("opened", str, str, db.Gallery)
    _open = CommandEntry("open", bool, str, str, db.Gallery)
    _resolve = CommandEntry("resolve", tuple, db.Gallery)

    def __init__(self):
        super().__init__()
        self.path = ""
        self.first_file = ""
        self.gallery = None

    @_open.default()
    def _open_gallery(parent, child, gallery):
        opened = False
        path = parent
        if child and config.send_path_to_first_file.value:
            path = child

        if config.external_image_viewer.value:
            args = tuple()
            if config.external_image_viewer_args.value:
                args = tuple(x.strip() for x in config.external_image_viewer_args.value.split())
            subprocess.Popen((config.external_image_viewer.value, path, *args))
            opened = True
        else:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', path))
            elif os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', path))
            opened = True

        return opened

    @_resolve.default()
    def _resolve_gallery(gallery):
        parent = ""
        child = ""
        if gallery.single_source:
            if gallery.pages.count():
                #TODO: when number 1 doesnt exist?
                first_page = gallery.pages.filter(db.Page.number==1)
                if first_page:
                    if first_page.in_archive:
                        pass
                    else:
                        child = pathlib.Path(first_page.path)
                        parent = pathlib.Path(os.path.split(first_page.path)[0])
        else:
            raise NotImplementedError

        return parent, child

    def main(self, gallery_id: int=None, gallery_obj: db.Gallery=None) -> bool:
        assert isinstance(gallery, db.Gallery) or isinstance(gallery_id, int)
        if gallery_id:
            gallery_obj = database_cmd.GetModelItemByID(db.Gallery, {gallery_id})
            if gallery_obj:
                gallery_obj = gallery_obj[0]
        self.gallery = gallery_obj

        with self._resolve.call(self.gallery) as plg:
            r = plg.first()
            if len(r) == 2:
                self.path, self.first_file = r

        with self._open.call(self.path, self.gallery) as plg:
            opened = plg.first()

        if opened:
            self._opened.emit(self.path, self.gallery)

        return opened
