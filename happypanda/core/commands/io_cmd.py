import pathlib
import os
from PIL import Image
from zipfile import ZipFile
from rarfile import RarFile
from collections import namedtuple

from happypanda.common import hlogger, exceptions, utils
from happypanda.core.command import CoreCommand, CommandEntry, AsyncCommand
from happypanda.core.services import ImageService
from happypanda.core import db
from happypanda.interface import enums


log = hlogger.Logger(__name__)

ImageProperties = namedtuple(
    "ImageProperties", [
        'size', 'radius', 'output_dir', 'output_path', 'name'])
ImageProperties.__new__.__defaults__ = (enums.ImageSize.Medium.value, 0, None, None, None)


class ImageItem(AsyncCommand):
    """

    Returns:
        a path to generated image
    """

    def __init__(self, service, filepath_or_bytes, properties):
        assert isinstance(service, ImageService)
        assert isinstance(properties, ImageProperties)
        super().__init__(service)
        self.properties = properties
        self._image = filepath_or_bytes

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, x):
        self._check_properties(x)
        self._properties = x

    def _check_properties(self, props):
        assert isinstance(props, ImageProperties)
        if props.size:
            assert isinstance(props.size, utils.ImageSize)

        if props.radius:
            assert isinstance(props.radius, int)

        if props.output_dir:
            assert isinstance(props.output_dir, str)

        if props.output_path:
            assert isinstance(props.output_path, str)

        if props.name:
            assert isinstance(props.name, str)

    def main(self) -> str:
        size = self.properties.size
        if isinstance(self._image, str):
            self._image = CoreFS(self._image).get()
        im = Image.open(self._image)
        f, ext = os.path.splitext(self._image)
        image_path = ""

        if self.properties.output_path:
            image_path = self.properties.output_path
            _f, _ext = os.path.splitext(image_path)
            if not _ext:
                image_path = os.path.join(_f, ext)

        elif self.properties.output_dir:
            o_dir = self.properties.output_dir
            o_name = self.properties.name if self.properties.name else utils.random_name()
            image_path = os.path.join(o_dir, o_name, ext)
        else:
            raise exceptions.CommandError(utils.this_command(self), "An output path or directory must be set for the generated image")

        if size.width and size.height:
            im.thumbnail(size.width, size.height)

        im.save(image_path)

        return image_path

    @staticmethod
    def gen_hash(model, size, item_id=None):
        """
        Generate a hash based on database model, image size and optionally item id
        """
        assert isinstance(model, db.Base)
        assert isinstance(size, utils.ImageSize)

        hash_str = model.__name__
        hash_str += str(tuple(size))
        hash_str += str(item_id) if item_id is not None else ''

        return hashlib.md5(hash_str.encode()).hexdigest()

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
        super().__init__()
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
        cls._get_commands()
        with cls._archive_formats.call() as plg:
            formats = set()
            for p in plg.all(default=True):
                formats.update(p)
            return tuple(formats)

    @classmethod
    def image_formats(cls):
        "Get supported image formats"
        cls._get_commands()
        with cls._image_formats.call() as plg:
            formats = set()
            for p in plg.all(default=True):
                formats.update(p)
            return tuple(formats)

    @property
    def name(self):
        "Get name of file or directory"
        return self._path.name

    @property
    def path(self):
        "Get path as string"
        return str(self._path)

    @property
    def archive_path(self):
        "Get path to the archive as string"
        if self.is_archive:
            return self.path
        elif self.inside_archive:
            parts = list(self._path.parents)
            while parts:
                p = parts.pop()
                if p.is_file() and p.suffix.lower() in self.archive_formats():
                    return str(p)
        return ""

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

    def get(self):
        "Get path as string. If path is inside an archive it will get extracted"
        
        if self.inside_archive:
            ap = self.archive_path
            af = CoreFS(ap)
            return str(af.extract(self.path[len(ap):]))
        else:
            return self.path

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

        if isinstance(filename, str):
            filename = (filename,)

        if self._archive:

            if not target:
                target = pathlib.Path(utils.create_temp_dir().name)

            if filename:
                p = []
                for f in filename:
                    p.append(CoreFS(self._archive.extract(f, target)))
                if len(p) == 1:
                    return p[0]
                else:
                    return CoreFS(target)
            else:
                self._archive.extract_all(target)
                return CoreFS(target)

        return ""

    def _resolve_path(self, p):
        if isinstance(p, CoreFS):
            self._path = p._path
            return
        self._path = p
        if isinstance(p, str):
            self._path = pathlib.Path(p)
        self._path = self._path.resolve()

        if self.is_archive:
            self._archive = Archive(self._path)

class Archive(CoreCommand):
    """
    Work with archive files

    Args:
        fpath: path to archive file

    """
    _init = CommandEntry('init', object, pathlib.Path)
    _test_corrupt = CommandEntry('test_corrupt', bool, object)

    _extract = CommandEntry("extract", str, object, str, pathlib.Path)
    _namelist = CommandEntry("namelist", tuple)

    def _def_formats():
        return ('.zip', '.rar', '.cbz', '.cbr')

    def __init__(self, fpath):
        self._path = pathlib.Path(fpath)
        self._ext = self._path.suffix.lower()
        if not self._path.exists():
            raise exceptions.ArchiveError("Archive file does not exist. File '{}' not found.".format(str(self._path)))
        if not self._path.suffix.lower() in CoreFS.archive_formats():
            raise exceptions.UnsupportedArchiveError(str(self._path))

        with self._init.call_capture(self._ext, self._path) as plg:
            self._archive = plg.first_or_none()

        if not self._archive:
            raise exceptions.CoreError(utils.this_function(), "No valid archive class found for this archive type: '{}'".format(self._ext))

        with self._test_corrupt.call_capture(self._ext, self._archive) as plg:
            r = plg.first_or_none()
            if r is not None:
                if r:
                    raise exceptions.BadArchiveError(str(self._path))

    @_test_corrupt.default(capture=True)
    def _test_corrupt_def(archive, capture=_def_formats()):
        if isinstance(archive, ZipFile):
            return bool(archive.testzip())
        elif isinstance(archive, RarFile):
            return bool(archive.testrar())

    @_init.default(capture=True)
    def _init_def(path, capture=_def_formats()):
        if path.suffix.lower() in ('.zip', '.cbz'):
            return ZipFile(str(path))
        elif path.suffix.lower() in ('.rar', '.cbr'):
            return RarFile(str(path))

    @_extract.default(capture=True)
    def _extract_def(archive, filename, target, capture=_def_formats()):
        temp_p = ""
        if isinstance(archive, ZipFile):
            membs = []
            for name in archive.namelist():
                if name.startswith(filename) and name != filename:
                    membs.append(name)
            temp_p = archive.extract(filename, str(target))
            for m in membs:
                archive.extract(m, str(target))
        elif isinstance(archive, RarFile):
            temp_p = target.join(filename)
            archive.extract(filename, str(target))
        return temp_p

    def extract(self, filename, target):
        """
        Extracts file from archive to target path
        Returns path to the extracted file
        """

        p = pathlib.Path(target)

        if not p.exists():
            raise exceptions.ExtractArchiveError("Target path does not exist: '{}'".format(str(p)))

        with self._extract.call_capture(self._ext, self._archive, filename, p) as plg:
            extract_path = plg.first()

        return pathlib.Path(extract_path)

    def extract_all(self, target):
        """
        Extracts all files to given path, and returns path
        """
        pass

class GalleryFS(CoreCommand):
    """
    Encapsulates an gallery object on the filesystem
    Args:
        path: a valid path to a valid gallery archive/folder
        db_gallery: Database Gallery object
    """

    def __init__(self, path, db_gallery=None):
        self.gallery = db_gallery
        self.path = CoreFS(path)
        self.name = ''
        self.title = ''
        self.artists = []
        self.language = ''
        self.convention = ''
        self.pages = {} # number : CoreFS

    #def load(self):
    #    "Extracts gallery data"
    #    _, self.name = os.path.split(self.path)
    #    info = GalleryScan.name_parser(self.path)
    #    self.title = info['title']
    #    self.artists.append(info['artist'])
    #    self.language = info['language']
    #    self.convention = info['convention']
    #    if self.gallery_type == utils.PathType.Directoy:
    #        self.pages = self._get_folder_pages()
    #    elif self.gallery_type == utils.PathType.Archive:
    #        self.pages = self._get_archive_pages()
    #    else:
    #        assert False, "this shouldnt happen... ({})".format(self.path)

    def get_gallery(self):
        "Creates/Updates database gallery"
        if not self.gallery:
            self.gallery = db.Gallery()

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