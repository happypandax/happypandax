import pathlib
import os
import hashlib

from io import BytesIO
from PIL import Image
from zipfile import ZipFile
from rarfile import RarFile
from collections import namedtuple
from contextlib import contextmanager
from gevent import fileobject

from happypanda.common import hlogger, exceptions, utils, constants
from happypanda.core.command import CoreCommand, CommandEntry, AsyncCommand
from happypanda.core.services import ImageService
from happypanda.core import db

log = hlogger.Logger(__name__)

ImageProperties = namedtuple(
    "ImageProperties", [
        'size', 'radius', 'output_dir', 'output_path', 'name', 'create_symlink'])
ImageProperties.__new__.__defaults__ = (utils.ImageSize(*constants.image_sizes['medium']), 0, None, None, None, True)


class ImageItem(AsyncCommand):
    """

    Returns:
        a path to generated image
    """

    def __init__(self, service, filepath_or_bytes, properties):
        assert isinstance(service, ImageService) or service is None
        assert isinstance(properties, ImageProperties)
        super().__init__(service, priority=constants.Priority.Low)
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

    def _convert(self, im, colormode="RGB"):
        if colormode == "RGB" or colormode == "RGBA":
            if im.mode == 'RGBA':
                return im
            if im.mode == "LA":
                return im.convert("RGBA")
            return im.convert(colormode)

        if colormode == "GRAY":
            return im.convert("L")
        return im.convert(colormode)

    def main(self) -> str:
        return self.run_native(self._generate).get()

    def _generate(self):
        size = self.properties.size
        if isinstance(self._image, str):
            fs = CoreFS(self._image)
            if not fs.exists:
                return ""
            self._image = fs.get()
        im = None
        image_path = ""
        try:
            im = self._convert(Image.open(self._image))
            f, ext = os.path.splitext(self._image)

            if self.properties.output_path:
                image_path = self.properties.output_path
                _f, _ext = os.path.splitext(image_path)
                if not _ext:
                    image_path = _f + ext

            elif self.properties.output_dir:
                o_dir = self.properties.output_dir
                o_name = self.properties.name if self.properties.name else utils.random_name()
                if not o_name.endswith(ext):
                    o_name = o_name + ext
                image_path = os.path.join(o_dir, o_name)
            else:
                image_path = BytesIO()

            save_image = True
            if size.width and size.height:
                if ext.lower().endswith(".gif"):
                    new_frame = Image.new('RGBA', im.size)
                    new_frame.paste(im, (0, 0), im.convert('RGBA'))
                    im.close()
                    im = new_frame
                im.thumbnail((size.width, size.height), Image.ANTIALIAS)

            else:
                if self.properties.create_symlink and isinstance(image_path, str):
                    image_path = image_path + constants.link_ext
                    with open(image_path, 'w', encoding='utf-8') as f:
                        f.write(self._image)
                    save_image = False

            if save_image:
                im.save(image_path)
        finally:
            if im:
                im.close()
        return image_path

    @staticmethod
    def gen_hash(model, size, item_id=None):
        """
        Generate a hash based on database model, image size and optionally item id
        """
        assert isinstance(model, db.Base) or issubclass(model, db.Base)
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

    def __init__(self, path=pathlib.Path(), archive=None):
        assert isinstance(path, (pathlib.Path, str, CoreFS))
        super().__init__()
        self._path = None
        self._o_path = path
        self._filetype = None
        self._archive = archive
        self._extacted_file = None
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
    def archive_name(self):
        "Get the full filename inside the archive"
        if self.inside_archive:
            self._init_archive()
            if isinstance(self._o_path, str) and self._archive.path_separator in self._o_path:
                parts = self._o_path.split(self._archive.path_separator)
            else:
                parts = list(self._path.parts)
            while parts:
                p = parts.pop(0)
                if p.lower().endswith(self.archive_formats()):
                    return self._archive.path_separator.join(parts)
        return ""

    @property
    def is_file(self):
        "Check if path is pointed to a file"
        return not self.is_dir

    @property
    def is_dir(self):
        "Check if path is pointed to a directory"
        if self.inside_archive:
            self._init_archive()
            return self._archive.is_dir(self.archive_name)
        else:
            return self._path.is_dir()

    @property
    def is_archive(self):
        "Check if path is pointed to an archive file"
        if self.ext in self.archive_formats():
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
        self._init_archive()
        if self.inside_archive:
            return self.archive_name in self._archive.namelist()
        else:
            return self._path.exists()

    @property
    def ext(self):
        "Get file extension. An empty string is returned if path is a directory"
        return self._path.suffix.lower()

    @property
    def count(self):
        "Get the amount of files and folders inside this path. 0 is returned if path is a file"
        raise NotImplementedError
        return self._path.suffix.lower()

    def contents(self):
        "If this is an archive or folder, return a tuple of CoreFS objects else return None"
        if self.is_archive:
            self._init_archive()
            root = self._archive.path_separator.join(self._path.parts)
            return tuple(CoreFS(self._archive.path_separator.join((root, x))) for x in self._archive.namelist())
        elif self.is_dir:
            if self.inside_archive:
                raise NotImplementedError
            else:
                return tuple(CoreFS(x) for x in self._path.iterdir())

    def get(self):
        "Get path as string. If path is inside an archive it will get extracted"
        self._init_archive()
        if self.inside_archive:
            if not self._extacted_file:
                self._extacted_file = self.extract()
            return self._extacted_file.path
        else:
            return self.path

    @contextmanager  # TODO: Make usable without contextmanager too
    def open(self, *args, **kwargs):
        self._init_archive()
        try:
            if self.inside_archive:
                f = self._archive.open(self.archive_name, *args, **kwargs)
            else:
                f = open(self.get(), *args, **kwargs)
            f = fileobject.FileObject(f)
        except PermissionError:
            if self.is_dir:
                raise exceptions.CoreError(utils.this_function(), "Tried to open a folder which is not possible")
            raise
        yield f
        f.close()

    def close(self):
        ""
        if self._archive:
            self._archive.close()

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
        self._init_archive()
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
                if self.inside_archive:
                    return CoreFS(self._archive.extract(self.archive_name, target))
                else:
                    self._archive.extract_all(target)
                    return CoreFS(target)
        return ""

    def _resolve_path(self, p):
        if isinstance(p, CoreFS):
            self._path = p._path
            self._o_path = p._o_path
            self._archive = p._archive
            self._filetype = p._filetype
            return
        self._path = p
        if isinstance(p, str):
            self._path = pathlib.Path(p)

        if not self.inside_archive:  # TODO: resolve only the parts not in archive
            if self._path.exists():
                self._path = self._path.resolve()

    def _init_archive(self):
        if not self._archive:
            if self.inside_archive or self.is_archive:
                self._archive = Archive(self.archive_path)

    def __lt__(self, other):
        if isinstance(other, CoreFS):
            return self.path < other.path
        return super().__lt__(other)


class Archive(CoreCommand):
    """
    Work with archive files

    Args:
        fpath: path to archive file

    """
    _init = CommandEntry('init', object, pathlib.Path)
    _path_sep = CommandEntry('path_sep', str, object)
    _test_corrupt = CommandEntry('test_corrupt', bool, object)
    _is_dir = CommandEntry('is_dir', bool, object, str)
    _extract = CommandEntry("extract", str, object, str, pathlib.Path)
    _namelist = CommandEntry("namelist", tuple, object)
    _open = CommandEntry("open", object, object, str, tuple, dict)
    _close = CommandEntry("close", None, object)

    def _def_formats():
        return (CoreFS.ZIP, CoreFS.RAR, CoreFS.CBZ, CoreFS.CBR)

    def __init__(self, fpath):
        self._opened = False
        self._archive = None
        self._path = pathlib.Path(fpath)
        self._ext = self._path.suffix.lower()
        if not self._path.exists():
            raise exceptions.ArchiveExistError(str(self._path))
        if not self._path.suffix.lower() in CoreFS.archive_formats():
            raise exceptions.ArchiveUnsupportedError(str(self._path))

        try:
            with self._init.call_capture(self._ext, self._path) as plg:
                self._archive = plg.first_or_none()

            if not self._archive:
                raise exceptions.CoreError(
                    utils.this_function(),
                    "No valid archive handler found for this archive type: '{}'".format(
                        self._ext))

            with self._test_corrupt.call_capture(self._ext, self._archive) as plg:
                r = plg.first_or_none()
                if r is not None:
                    if r:
                        raise exceptions.ArchiveCorruptError(str(self._path))

            with self._path_sep.call_capture(self._ext, self._archive) as plg:
                p = plg.first_or_none()
                self.path_separator = p if p else '/'
        except:
            if self._archive:
                self.close()
            raise

    def __del__(self):
        if hasattr(self, '_archive') and self._archive:
            self.close()

    @_test_corrupt.default(capture=True)
    def _test_corrupt_def(archive, capture=_def_formats()):
        if isinstance(archive, ZipFile):
            return bool(archive.testzip())
        elif isinstance(archive, RarFile):
            return bool(archive.testrar())

    @_init.default(capture=True)
    def _init_def(path, capture=_def_formats()):
        if path.suffix.lower() in ('.zip', '.cbz'):
            o = ZipFile(str(path))
        elif path.suffix.lower() in ('.rar', '.cbr'):
            o = RarFile(str(path))
        o.hpx_path = path
        return o

    @_namelist.default(capture=True)
    def _namelist_def(archive, capture=_def_formats()):
        filelist = archive.namelist()
        return filelist

    @_is_dir.default(capture=True)
    def _is_dir_def(archive, filename, capture=_def_formats()):
        if not filename:
            return False
        if filename not in Archive._namelist_def(archive) and filename + '/' not in Archive._namelist_def(archive):
            raise exceptions.ArchiveFileNotFoundError(filename, archive.hpx_path)
        if isinstance(archive, ZipFile):
            if filename.endswith('/'):
                return True
        elif isinstance(archive, RarFile):
            info = archive.getinfo(filename)
            return info.isdir()
        return False

    @_extract.default(capture=True)
    def _extract_def(archive, filename, target, capture=_def_formats()):
        temp_p = ""
        if isinstance(archive, ZipFile):
            membs = []
            for name in Archive._namelist_def(archive):
                if name.startswith(filename) and name != filename:
                    membs.append(name)
            temp_p = archive.extract(filename, str(target))
            for m in membs:
                archive.extract(m, str(target))
        elif isinstance(archive, RarFile):
            temp_p = target.join(filename)
            archive.extract(filename, str(target))
        return temp_p

    @_open.default(capture=True)
    def _open_def(archive, filename, args, kwargs, capture=_def_formats()):
        if filename not in Archive._namelist_def(archive):
            raise exceptions.ArchiveFileNotFoundError(filename, archive.hpx_path)
        return archive.open(filename, *args, **kwargs)

    @_close.default(capture=True)
    def _close_def(archive, capture=_def_formats()):
        archive.close()

    def namelist(self):
        ""
        with self._namelist.call_capture(self._ext, self._archive) as plg:
            return plg.first()

    def is_dir(self, filename):
        """
        Checks if the provided name in the archive is a directory or not
        """
        with self._is_dir.call_capture(self._ext, self._archive, filename) as plg:
            return plg.first()

    def extract(self, filename, target):
        """
        Extracts file from archive to target path
        Returns path to the extracted file
        """

        p = pathlib.Path(target)

        if not p.exists():
            raise exceptions.ArchiveExtractError("Target path does not exist: '{}'".format(str(p)))

        with self._extract.call_capture(self._ext, self._archive, filename, p) as plg:
            extract_path = plg.first()

        return pathlib.Path(extract_path)

    def extract_all(self, target):
        """
        Extracts all files to given path, and returns path
        """
        pass

    def open(self, filename, *args, **kwargs):
        """
        Open file in archive, returns a file-like object.
        """
        with self._open.call_capture(self._ext, self._archive, filename, args, kwargs) as plg:
            r = plg.first()
            if not hasattr(r, 'read') or not hasattr(r, 'write'):
                raise exceptions.PluginHandlerError(plg.get_node(0), "Expected a file-like object from archive.open")
            return r

    def close(self):
        """
        Close archive, releases all open resources
        """
        with self._close.call_capture(self._ext, self._archive) as plg:
            plg.first()


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
        self.pages = {}  # number : CoreFS

    # def load(self):
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
                CoreFS.image_formats())]
        for n, x in enumerate(sorted(dir_images), 1):
            pages.append((n, os.path.abspath(x)))
        return pages

    def _get_archive_pages(self):
        ""
        raise NotImplementedError
