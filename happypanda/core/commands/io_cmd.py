import pathlib
import os

from happypanda.common import hlogger
from happypanda.core.command import CoreCommand, CommandEntry

log = hlogger.Logger(__name__)

class CoreFS(CoreCommand):
    """
    Encapsulates path on the filesystem

    Default supported archive types are:
        ZIP, RAR, CBR and CBZ

    Default supported image types are:
        JPG/JPEG, BMP, PNG and GIF
    
    """

    ZIP = '.zip'
    RAR = '.rar'
    CBR = '.cbr'
    CBZ = '.cbz'

    JPG = '.jpg'
    JPEG = '.jpeg'
    BMP = '.bmp'
    PNG = '.png'
    GIF = '.gif'

    _archive_formats = CommandEntry("archive_formats", tuple)
    _image_formats = CommandEntry("image_formats", tuple)

    def __init__(self, path = pathlib.Path()):
        assert isinstance(path, (pathlib.Path, str, CoreFS))
        super().__init()
        self._path = None
        self._filetype = None
        self._archive = None
        self._resolve_path(path)

    @_archive_formats.default()
    def _archive_formats_def():
        return (CoreFS.ZIP, CoreFS.RAR, CoreFS.CBR, CoreFS.CBZ)

    @_image_formats.default()
    def _image_formats_def():
        return (CoreFS.JPG, CoreFS.JPEG, CoreFS.BMP, CoreFS.PNG, CoreFS.GIF)

    @classmethod
    def archive_formats(cls):
        "Get supported archive formats"
        with cls._archive_formats.call() as plg:
            formats = set()
            for p in plg.all(default=True):
                formats.update(p)
            return formats

    @classmethod
    def image_formats(cls):
        "Get supported image formats"
        with cls._image_formats.call() as plg:
            formats = set()
            for p in plg.all(default=True):
                formats.update(p)
            return formats

    @property
    def path(self):
        "Get path as string"
        return str(self._path)

    @property
    def is_file(self):
        "Check if path is pointed to a file"
        return not self.is_dir

    @property
    def is_dir(self):
        "Check if path is pointed to a directory"
        return self._path.is_dir()

    @property
    def is_archive(self):
        "Check if path is pointed to an archive file"
        if self.is_file and self.ext in self.archive_formats():
            return True
        return False

    @property
    def inside_archive(self):
        "Check if path is pointed to an object inside an archive"
        parts = list(self._path.parents)

        while parts:
            p = parts.pop()
            if p.is_file() and p.suffix.lower() in self.archive_formats():
                return True
        return False

    @property
    def is_image(self):
        "Check if path is pointed to an image file"
        if self.is_file and self.ext in self.image_formats():
            return True
        return False

    @property
    def exists(self):
        "Check if path exists"
        return self._path.exists()
    
    @property
    def ext(self):
        "Get file extension. An empty string is returned if path is a directory"
        return self._path.suffix.lower()

    @property
    def count(self):
        "Get the amount of files and folders inside this path. 0 is returned if path is a file"
        return self._path.suffix.lower()

    @classmethod
    def get(cls):
        "Get path as string. If path is inside an archive it will get extracted"
        pass

    def extract(self, filename=None, target=None):
        """
        Extract files if path is an archive

        Args:
            filename: a string or a tuple of strings of contents inside the archive, leave None to extract all contents
            target: a path to where contents will be extracted to, leave None to use a temp directory

        Returns:
            a CoreFS object pointed to the extracted files
        """
        assert isinstance(filename, (str, tuple)) or filename is None
        assert isinstance(target, str) or target is None

    def _resolve_path(self, p):
        if isinstance(p, CoreFS):
            self._path = p._path
            return
        self._path = p
        if isinstance(p, str):
            self._path = pathlib.Path(p)
        self._path = self._path.resolve()

        if self.exists():
            pass

class GalleryFS(CoreCommand):
    """
    Encapsulates an gallery object on the filesystem
    Params:
        path -- a valid path to a valid gallery archive/folder
        path_in_archive -- path to gallery inside of archive
        db_gallery -- Database Gallery object
    """

    def __init__(self, ):
        self._gallery_type = utils.PathType.check(path)
        self.gallery = db_gallery
        self.path = path
        self.path_in_archive = path_in_archive
        self.name = ''
        self.title = ''
        self.artists = []
        self.language = ''
        self.convention = ''
        self.pages = []  # tuples: (number, page_file)

    def load(self):
        "Extracts gallery data"
        _, self.name = os.path.split(self.path)
        info = GalleryScan.name_parser(self.path)
        self.title = info['title']
        self.artists.append(info['artist'])
        self.language = info['language']
        self.convention = info['convention']
        if self.gallery_type == utils.PathType.Directoy:
            self.pages = self._get_folder_pages()
        elif self.gallery_type == utils.PathType.Archive:
            self.pages = self._get_archive_pages()
        else:
            assert False, "this shouldnt happen... ({})".format(self.path)

    def get_gallery(self):
        "Creates/Updates database gallery"
        if not self.gallery:
            self.gallery = db.Gallery()

        self.gallery.path = self.path
        self.gallery.path_in_archive = self.path_in_archive
        self.gallery.in_archive = True if self.gallery_type == utils.PathType.Archive else False
        t = db.Title(name=self.title)
        # TODO: add language to title
        for x in self.gallery.titles:
            if x.name == t.name:
                t = x
                break
        self.gallery.titles.append(t)
        [self.gallery.artists.append(
            db.Artist(name=x).exists(True, True)) for x in self.artists]
        db_pages = self.gallery.pages.count()
        if db_pages != len(self.pages):
            if db_pages:
                self.gallery.pages.delete()
            [self.gallery.pages.append(
                db.Page(path=x[1], number=x[0])) for x in self.pages]

        return self.gallery

    def _get_folder_pages(self):
        ""
        pages = []
        dir_images = [
            x.path for x in os.scandir(
                self.path) if not x.is_dir() and x.name.endswith(
                constants.supported_images)]
        for n, x in enumerate(sorted(dir_images), 1):
            pages.append((n, os.path.abspath(x)))
        return pages

    def _get_archive_pages(self):
        ""
        raise NotImplementedError