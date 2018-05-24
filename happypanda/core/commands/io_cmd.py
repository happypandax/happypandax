"""
I/O CMD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: happypanda.core.commands.io_cmd.ImageProperties
    :members:

"""
import pathlib
import os
import hashlib
import shutil
import send2trash
import attr
import subprocess
import imghdr
import errno

from io import BytesIO
from PIL import Image
from zipfile import ZipFile
from rarfile import RarFile
from tarfile import TarFile
from contextlib import contextmanager
from gevent import fileobject

from happypanda.common import hlogger, exceptions, utils, constants
from happypanda.core.command import CoreCommand, CommandEntry, AsyncCommand, Command, CParam
from happypanda.core.services import ImageService
from happypanda.core import db

log = hlogger.Logger(constants.log_ns_command + __name__)


@attr.s
class ImageProperties:
    #: size of image, a :data:`.utils.ImageSize` object
    size: utils.ImageSize = attr.ib(default=utils.ImageSize(*constants.image_sizes['medium']))
    #: corner radius
    radius: int = attr.ib(default=0)
    #: folder to save the image to
    output_dir: str = attr.ib(default=None)
    #: path to save the image to, this and ``output_dir`` are mutually exclusive
    output_path: str = attr.ib(default=None)
    #: name of image file when saved to ``output_dir``, else a random name will be generated
    name: str = attr.ib(default=None)
    #: create an artificial symlink til the source image instead of copying it (only useful if image size isn't modified)
    create_symlink: bool = attr.ib(default=True)


class ImageItem(AsyncCommand):
    """
    Generate an image from source image

    Args:
        filepath_or_bytes: path to image file or a ``bytes`` object
        properties: an :class:`.ImageProperties` object
        service: service to put this async command into

    Returns:
        a path to generated image
    """

    def __init__(self, filepath_or_bytes, properties, service=None):
        assert isinstance(service, ImageService) or service is None
        assert isinstance(properties, ImageProperties)
        if service is None:
            service = ImageService.generic
        super().__init__(service, priority=constants.Priority.Low)
        self.properties = properties
        self._image = filepath_or_bytes
        self._retrying = False

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

    def _convert(self, im, colormode="RGB", img_ext=None):
        if colormode == "RGB" or colormode == "RGBA":
            if im.mode == 'RGBA' and img_ext not in ('.jepg', '.jpg'):
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
        log.d("Generating image thumbnail", self._image,
              self.properties)
        self.set_max_progress(2)
        self.set_progress(1)
        size = self.properties.size
        fs = None
        if isinstance(self._image, str):
            fs = CoreFS(self._image)
            if not fs.exists:
                log.d("Image file does not exists")
                return ""
            self._image = fs.get()
        im = None
        image_path = ""
        try:
            if isinstance(self._image, str):
                _, ext = os.path.splitext(self._image)
                if self._retrying:
                    ext = '.' + imghdr.what(self._image)
            else:
                ext = '.' + imghdr.what("", self._image)

            im = Image.open(self._image)
            im = self._convert(im, img_ext=ext)

            if self.properties.output_path:
                image_path = self.properties.output_path
                _f, _ext = os.path.splitext(image_path)
                if not _ext:
                    image_path = _f + ext

            elif self.properties.output_dir:
                o_dir = self.properties.output_dir
                if not os.path.exists(o_dir):
                    os.makedirs(o_dir)
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
                    if fs and fs.inside_archive:
                        pathlib.Path(self._image).rename(image_path)
                    else:
                        image_path = image_path + constants.link_ext
                        with open(image_path, 'w', encoding='utf-8') as f:
                            f.write(self._image)
                    save_image = False

            if save_image:
                im.save(image_path)
        except (OSError, KeyError) as e:
            if not self._retrying:
                log.w("Failed generating image:", e.args, "retrying...")
                self._retrying = True
                if im:
                    im.close()
                    im = None
                return self._generate()
            log.w("Failed generating image:", e.args)
        finally:
            if im:
                im.close()
        log.d("Generated image path:", image_path)
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
        ZIP, RAR, CBR, CBZ, TAR.GZ, TAR.BZ2 and TAR.XZ

    Default supported image types are:
        JPG/JPEG, BMP, PNG and GIF

    Args:
        path: path to file on the filesystem, accepts ``str``, ``pathlib.Path`` and :class:``.CoreFS`` objetcs
        archive: if ``path`` is an archive or is inside one, then this :class:`.Archive` object should be used instead of creating a new one
    """

    ZIP = '.zip'
    RAR = '.rar'
    CBR = '.cbr'
    CBZ = '.cbz'
    TARGZ = '.tar.gz'
    TARBZ2 = '.tar.bz2'
    TARXZ = '.tar.xz'

    JPG = '.jpg'
    JPEG = '.jpeg'
    BMP = '.bmp'
    PNG = '.png'
    GIF = '.gif'

    _archive_formats: tuple = CommandEntry("archive_formats",
                                           __doc="""
                                           Called to get a tuple of supported archive file formats
                                           """,
                                           __doc_return="""
                                           a tuple of archive formats
                                           """)
    _image_formats: tuple = CommandEntry("image_formats",
                                         __doc="""
                                         Called to get a tuple of supported image formats
                                         """,
                                         __doc_return="""
                                         a tuple of image formats
                                         """)

    def __init__(self, path: str=pathlib.Path(), archive=None):
        assert isinstance(path, (pathlib.Path, str, CoreFS))
        assert isinstance(archive, Archive) or archive is None
        super().__init__()
        self._path = None
        self._o_path = path
        self._filetype = None
        self._archive = archive
        self._extacted_file = None
        self._resolve_path(path)

    @_archive_formats.default()
    def _archive_formats_def():
        return (CoreFS.ZIP, CoreFS.RAR, CoreFS.CBR, CoreFS.CBZ, CoreFS.TARGZ,
                CoreFS.TARBZ2, CoreFS.TARXZ)

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
        log.d("Checking if path is inside archive", self._path)
        parts = list(self._path.parents)

        while parts:
            p = parts.pop()
            if p.is_file() and p.suffix.lower() in self.archive_formats():
                log.d("Path is inside an archive", self._path)
                return True
        log.d("Path is not inside an archive", self._path)
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
        try:
            if self.inside_archive:
                self._init_archive()
                log.d("Checking for archive path", self.archive_name, "in archive", self.path)
                return self.archive_name in self._archive.namelist()
            else:
                return self._path.exists()
        except OSError as e:
            if e.errno == errno.ENXIO:
                return False
            raise

    @property
    def ext(self):
        "Get file extension. An empty string is returned if path is a directory"
        suffixes = self._path.suffixes
        while suffixes:
            s = "".join(suffixes)
            if s.lower() in self.archive_formats():
                break
            suffixes.pop(0)
        else:
            s = self._path.suffix

        return s.lower()

    @property
    def count(self):
        "Get the amount of files and folders inside this path. 0 is returned if path is a file"
        raise NotImplementedError
        return self._path.suffix.lower()

    def contents(self, corefs=True):
        "If this is an archive or folder, return a tuple of CoreFS objects else return None"
        if self.is_archive:
            self._init_archive()
            root = self._archive.path_separator.join(self._path.parts)
            l = tuple(self._archive.path_separator.join((root, x)) for x in self._archive.namelist())
        elif self.is_dir:
            if self.inside_archive:
                raise NotImplementedError
            else:
                l = tuple(x for x in self._path.iterdir())
        if corefs:
            l = tuple(CoreFS(x) for x in l)
        return l

    def get(self, target=None):
        "Get path as string. If path is inside an archive it will get extracted"
        if self.inside_archive:
            self._init_archive()
            if not self._extacted_file:
                self._extacted_file = self.extract(target=target)
            return self._extacted_file.path
        else:
            return self.path

    def delete(self, ignore_errors=False, send_to_trash=False):
        "Delete path"
        if self.is_archive or self.inside_archive:
            raise NotImplementedError
        try:
            if send_to_trash:
                send2trash.send2trash(self.path)
            else:
                if self._path.is_dir():
                    shutil.rmtree(str(self._path))
                else:
                    self._path.unlink()
        except BaseException:
            if ignore_errors:
                log.exception("Error raised while trying to delete:", self._path)
            else:
                raise

    @contextmanager  # TODO: Make usable without contextmanager too
    def open(self, *args, **kwargs):
        ""
        try:
            if self.inside_archive:
                self._init_archive()
                f = self._archive.open(self.archive_name, *args, **kwargs)
            else:
                f = open(self.get(), *args, **kwargs)
            f = fileobject.FileObjectThread(f, mode=f.mode)
        except PermissionError:
            if self.is_dir:
                raise exceptions.CoreError(utils.this_function(), "Tried to open a folder which is not possible")
            raise
        yield f
        f.close()

    @staticmethod
    def open_with_default(path):
        "Open path with the default application"
        if constants.is_osx:
            subprocess.call(('open', path))
        elif constants.is_win:
            os.startfile(path)
        elif constants.is_linux:
            subprocess.call(('xdg-open', path))

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
        raise exceptions.NotAnArchiveError(self.path)

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

    def _init_archive(self):
        if not self._archive:
            if self.inside_archive or self.is_archive:
                self._archive = Archive(self.archive_path)

    def __lt__(self, other):
        if isinstance(other, CoreFS):
            return self.path < other.path
        return super().__lt__(other)

    def __str__(self):
        return "CoreFS({})".format(self.path)

    def __repr__(self):
        return "CoreFS({})".format(self.path)


class Archive(CoreCommand):
    """
    Work with archive files

    Args:
        fpath: path to archive file

    """
    _init: object = CommandEntry('init',
                                 CParam("path", pathlib.Path, "path to file"),
                                 __capture=(str, "file extension"),
                                 __doc="""
                                 Called to initialize the underlying archive object
                                 """,
                                 __doc_return="""
                                 the underlying archive object
                                 """
                                 )
    _path_sep: str = CommandEntry('path_sep',
                                  CParam("archive", object, "the underlying archive object"),
                                  __capture=(str, "file extension"),
                                  __doc="""
                                  Called to retrieve the character that separates path name components.
                                  The default separator is ``/``
                                  """,
                                  __doc_return="""
                                  path separator character
                                  """
                                  )
    _test_corrupt: bool = CommandEntry('test_corrupt',
                                      CParam("archive", object, "the underlying archive object"),
                                      __capture=(str, "file extension"),
                                      __doc="""
                                      Called to test if the archive is corrupted
                                      """,
                                      __doc_return="""
                                      whether the archive is corrupt or not
                                      """
                                      )
    _is_dir: bool = CommandEntry('is_dir',
                                CParam("archive", object, "the underlying archive object"),
                                CParam("filename", str, "filename or path **inside** the archive"),
                                __capture=(str, "file extension"),
                                __doc="""
                                Called to check if an item inside the archive is a directory
                                """,
                                __doc_return="""
                                whether the item is a directory or not
                                """
                                )
    _extract: str = CommandEntry("extract",
                                CParam("archive", object, "the underlying archive object"),
                                CParam("filename", str, "filename or path **inside** the archive"),
                                CParam("target", pathlib.Path, "target path to where items should be extracted to"),
                                __capture=(str, "file extension"),
                                __doc="""
                                Called to extract an item inside the archive
                                """,
                                __doc_return="""
                                path to extracted content
                                """)
    _extract_all: str = CommandEntry("extract_all",
                                    CParam("archive", object, "the underlying archive object"),
                                    CParam("target", pathlib.Path, "target path to where items should be extracted to"),
                                    __capture=(str, "file extension"),
                                    __doc="""
                                    Called to extract all items inside the archive
                                    """,
                                    __doc_return="""
                                    path to extracted content
                                    """)
    _namelist: tuple = CommandEntry("namelist",
                                    CParam("archive", object, "the underlying archive object"),
                                    __capture=(str, "file extension"),
                                    __doc="""
                                    Called to retrieve a tuple of the files and folders in the archive
                                    """,
                                    __doc_return="""
                                    a tuple of the files and folders in the archive
                                    """)
    _open: object = CommandEntry("open",
                                CParam("archive", object, "the underlying archive object"),
                                CParam("filename", str, "filename or path **inside** the archive"),
                                CParam("args", tuple, "additional arguments to pass when opening the file (like ``encoding='utf-8'``, etc.)"),
                                CParam("kwargs", dict, "additional keyword-arguments to pass when opening the file (like ``encoding='utf-8'``, etc.)"),
                                __capture=(str, "file extension"),
                                __doc="""
                                Called to open a file inside the archive.
                                """,
                                __doc_return="""
                                a file-like object
                                """
                                )
    _close: None = CommandEntry("close",
                                CParam("archive", object, "the underlying archive object"),
                                __capture=(str, "file extension"),
                                __doc="""
                                Called to close the underlying archive object
                                """)

    def _def_formats():
        return (CoreFS.ZIP, CoreFS.RAR, CoreFS.CBZ, CoreFS.CBR, CoreFS.TARBZ2,
                CoreFS.TARGZ, CoreFS.TARXZ)

    def __init__(self, fpath: str):
        self._opened = False
        self._archive = None
        self._path = pathlib.Path(fpath)
        self._pathfs = CoreFS(fpath)
        self._ext = self._pathfs.ext
        if not self._path.exists():
            raise exceptions.ArchiveExistError(str(self._path))
        if self._pathfs.ext not in CoreFS.archive_formats():
            raise exceptions.ArchiveUnsupportedError(str(self._path))

        try:
            with self._init.call_capture(self._ext, self._path) as plg:
                self._archive = plg.first_or_none()

            if not self._archive:
                raise exceptions.CoreError(
                    utils.this_function(),
                    "No valid archive handler found for this archive type: '{}'".format(
                        self._ext))

            with self._path_sep.call_capture(self._ext, self._archive) as plg:
                p = plg.first_or_none()
                self.path_separator = p if p else '/'
        except BaseException:
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
        elif isinstance(archive, TarFile):
            return False

    @_init.default(capture=True)
    def _init_def(path, capture=_def_formats()):
        if path.suffix.lower() in ('.zip', '.cbz'):
            o = ZipFile(str(path))
        elif path.suffix.lower() in ('.rar', '.cbr'):
            o = RarFile(str(path))
        elif CoreFS(path).ext in (CoreFS.TARBZ2, CoreFS.TARGZ, CoreFS.TARXZ):
            o = TarFile.open(str(path))
        o.hpx_path = path
        return o

    @_namelist.default(capture=True)
    def _namelist_def(archive, capture=_def_formats()):
        if isinstance(archive, TarFile):
            filelist = archive.getnames()
        else:
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
        elif isinstance(archive, TarFile):
            try:
                info = archive.getmember(filename)
                return info.isdir()
            except KeyError:
                raise exceptions.ArchiveFileNotFoundError(filename, archive.hpx_path)
        return False

    @_extract.default(capture=True)
    def _extract_def(archive, filename, target, capture=_def_formats()):
        temp_p = str(target)
        if isinstance(archive, ZipFile):
            membs = []
            for name in Archive._namelist_def(archive):
                if name.startswith(filename) and name != filename:
                    membs.append(name)
            temp_p = archive.extract(filename, str(target))
            for m in membs:
                archive.extract(m, str(target))
        elif isinstance(archive, RarFile):
            temp_p = str(target.joinpath(filename))
            archive.extract(filename, str(target))
        elif isinstance(archive, TarFile):
            try:
                info = archive.getmember(filename)
                archive.extractall(target, [info])
            except KeyError:
                raise exceptions.ArchiveFileNotFoundError(filename, archive.hpx_path)
        return temp_p

    @_extract_all.default(capture=True)
    def _extract_all_def(archive, target, capture=_def_formats()):
        target_p = str(target)
        if isinstance(archive, (ZipFile, RarFile, TarFile)):
            archive.extractall(target_p)
        return target_p

    @_open.default(capture=True)
    def _open_def(archive, filename, args, kwargs, capture=_def_formats()):
        if filename not in Archive._namelist_def(archive):
            raise exceptions.ArchiveFileNotFoundError(filename, archive.hpx_path)
        return archive.open(filename, *args, **kwargs)

    @_close.default(capture=True)
    def _close_def(archive, capture=_def_formats()):
        archive.close()

    def test(self):
        with self._test_corrupt.call_capture(self._ext, self._archive) as plg:
            r = plg.first_or_none()
            if r is not None and r:
                raise exceptions.ArchiveCorruptError(str(self._path))

    def _normalize_filename(self, f):
        f = f.replace('/', self.path_separator)
        f = f.replace('\\', self.path_separator)
        return f

    def namelist(self):
        ""
        with self._namelist.call_capture(self._ext, self._archive) as plg:
            return plg.first()

    def is_dir(self, filename):
        """
        Checks if the provided name in the archive is a directory or not
        """
        filename = self._normalize_filename(filename)
        with self._is_dir.call_capture(self._ext, self._archive, filename) as plg:
            return plg.first()

    def extract(self, filename, target):
        """
        Extracts file from archive to target path
        Returns path to the extracted file
        """
        filename = self._normalize_filename(filename)
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
        p = pathlib.Path(target)

        if not p.exists():
            raise exceptions.ArchiveExtractError("Target path does not exist: '{}'".format(str(p)))

        with self._extract_all.call_capture(self._ext, self._archive, p) as plg:
            extract_path = plg.first()

        return pathlib.Path(extract_path)

    def open(self, filename, *args, **kwargs):
        """
        Open file in archive, returns a file-like object.
        """
        filename = self._normalize_filename(filename)
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
        path_or_dbitem: path to a valid gallery archive/folder or a :class:`.db.Gallery` database item
    """

    def __init__(self, path_or_dbitem: str):
        assert isinstance(path_or_dbitem, (str, CoreFS, db.Gallery, pathlib.Path))

        self.gallery = None
        self.path = None
        self.name = ''
        self.title = ''
        self.artists = []
        self.language = ''
        self.convention = ''
        self.pages = {}  # number : CoreFS

        if isinstance(path_or_dbitem, db.Gallery):
            self.gallery = path_or_dbitem
        else:
            self.path = CoreFS(path_or_dbitem)

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


class NameParser(Command):
    """
    """

    #parse = CommandEntry("rename", None, str, str)

    def __init__(self):
        super().__init__()
        self.parsed = {}
