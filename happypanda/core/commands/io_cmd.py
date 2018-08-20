"""
.I/O
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
import typing
import regex
import langcodes
import weakref

from io import BytesIO
from PIL import Image
from zipfile import ZipFile
from rarfile import RarFile
from tarfile import TarFile
from gevent import fileobject
from natsort import natsorted
from ordered_set import OrderedSet
from cachetools.func import ttl_cache

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
        if isinstance(self._image, (str, CoreFS)):
            fs = CoreFS(self._image)
            if not fs.exists:
                log.d("Image file does not exists")
                return ""
        fs_bytes = None
        im = None
        image_path = ""
        try:
            if isinstance(self._image, (str, CoreFS)):
                fs_bytes = fs.open("rb")
                _, ext = os.path.splitext(fs.path)
                if self._retrying and not fs.archive_type:
                    ext = '.' + imghdr.what(None, h=fs_bytes)
            else:
                fs_bytes = self._image
                ext = '.' + imghdr.what(None, h=fs_bytes)

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
            use_original = False
            if size.width or size.height:
                im = Image.open(fs_bytes)
                im_size = (size.width or 999999999, size.height or 999999999)
                if im.size > im_size:
                    im = self._convert(im, img_ext=ext)

                    if ext.lower().endswith(".gif"):
                        new_frame = Image.new('RGBA', im.size)
                        new_frame.paste(im, (0, 0), im.convert('RGBA'))
                        im.close()
                        im = new_frame
                    im.thumbnail(im_size, Image.ANTIALIAS)
                else:
                    use_original = True
            else:
                use_original = True

            if use_original and self.properties.create_symlink and isinstance(image_path, str):
                image_path = image_path + constants.link_ext
                with open(image_path, 'w', encoding='utf-8') as f:
                    f.write(fs.path)
                save_image = False

            if save_image and im:
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
            if fs_bytes:
                fs_bytes.close()
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
    TGZ = '.tgz'
    TARBZ2 = '.tar.bz2'
    TBZ = '.tbz'
    TARXZ = '.tar.xz'
    TXZ = '.txz'

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

    class _File:
        def __init__(self, corefs, mode="r", *args, **kwargs):
            self.corefs = corefs
            self.args = (mode, *args)
            self.kwargs = kwargs
            self.fp = self.corefs._open(*self.args, **self.kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            if self.fp:
                self.fp.close()

        def __getattr__(self, key):
            return getattr(self.fp, key)

        def __getitem__(self, item):
            return self.fp.__getitem__(item)

        def __setitem__(self, key, value):
            return self.fp.__setitem__(key, value)

    def __init__(self, path: str=pathlib.Path(), archive=None):
        assert isinstance(path, (pathlib.Path, str, CoreFS))
        assert isinstance(archive, Archive) or archive is None
        super().__init__()
        self._path = None
        self._o_path = path
        self._filetype = None
        self._archive = archive
        self._extacted_file = None
        self._ext = None
        if isinstance(path, str) and utils.is_url(path, strict=True):
            raise NotImplementedError("URLs are not supported yet")
        self._resolve_path(path)

    @_archive_formats.default()
    def _archive_formats_def():
        return Archive._def_formats()

    @_image_formats.default()
    def _image_formats_def():
        return (CoreFS.JPG, CoreFS.JPEG, CoreFS.BMP, CoreFS.PNG, CoreFS.GIF)

    @classmethod
    @ttl_cache()
    def archive_formats(cls):
        "Get supported archive formats"
        cls._get_commands()
        with cls._archive_formats.call() as plg:
            formats = set()
            for p in plg.all(default=True):
                formats.update(p)
            return tuple(formats)

    @classmethod
    @ttl_cache()
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
    def parent(self):
        "Get path to parent folder or file as string"
        return str(self._path.parent)

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
    def archive_type(self):
        "Return the archive ext if this file is an archive or is inside one"
        suffixes = self._path.suffixes
        while suffixes:
            s = "".join(suffixes)
            if s.lower() in self.archive_formats():
                return s.lower()
        return None

    @property
    def inside_archive(self):
        "Check if path is pointed to an object inside an archive"
        #log.d("Checking if path is inside archive", self._path)
        parts = list(self._path.parents)

        while parts:
            p = parts.pop()
            if p.is_file() and p.suffix.lower() in self.archive_formats():
                #log.d("Path is inside an archive", self._path)
                return True
        #log.d("Path is not inside an archive", self._path)
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
                #log.d("Checking for archive path", self.archive_name, "in archive", self.path)
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
        if self._ext is not None:
            return self._ext
        suffixes = self._path.suffixes
        while suffixes:
            s = "".join(suffixes)
            if s.lower() in self.archive_formats():
                break
            suffixes.pop(0)
        else:
            s = self._path.suffix

        self._ext = s.lower()
        return self._ext

    @property
    def count(self):
        "Get the amount of files and folders inside this path. 0 is returned if path is a file"
        raise NotImplementedError
        return self._path.suffix.lower()

    def contents(self, corefs=True) -> typing.Tuple[typing.Union[str, object]]:
        "If this is an archive or folder, return a tuple of CoreFS/str objects"
        if self.is_archive:
            self._init_archive()
            root = self._archive.path_separator.join(self._path.parts)
            l = tuple(self._archive.path_separator.join((root, x)) for x in self._archive.namelist())
        elif self.is_dir:
            if self.inside_archive:
                raise NotImplementedError
            else:
                l = tuple(str(x) for x in self._path.iterdir())
        if corefs:
            l = tuple(CoreFS(x, archive=self._archive) for x in l)
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

    def _open(self, mode="r", *args, **kwargs):
        ""
        try:
            if self.inside_archive:
                self._init_archive()
                f = self._archive.open(self.archive_name, mode, *args, **kwargs)
            else:
                f = open(self.get(), mode, *args, **kwargs)
            f = fileobject.FileObjectThread(f, mode=f.mode)
        except PermissionError:
            if self.is_dir:
                raise exceptions.CoreError(utils.this_function(), "Tried to open a folder which is not possible")
            raise
        return f

    def open(self, mode="r", *args, **kwargs):
        return self._File(self, mode, *args, **kwargs)

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
                constants.task_command.temp_cleaner.wake_up()
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
        return self.path

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
                                 CParam(
                                     "args", tuple, "additional arguments to pass when opening the file (like ``encoding='utf-8'``, etc.)"),
                                 CParam(
                                     "kwargs",
                                     dict,
                                     "additional keyword-arguments to pass when opening the file (like ``encoding='utf-8'``, etc.)"),
                                 __capture=(str, "file extension"),
                                 __doc="""
                                Called to open a file inside the archive. Please note that mode='r' refers to binary mode
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

    _archive_cache = weakref.WeakValueDictionary()
    _archive_obj_ref_count = {}

    def _def_formats():
        return (CoreFS.ZIP, CoreFS.RAR, CoreFS.CBZ, CoreFS.CBR,
                CoreFS.TARBZ2, CoreFS.TARGZ, CoreFS.TARXZ,
                CoreFS.TBZ, CoreFS.TGZ, CoreFS.TXZ)

    def __init__(self, fpath: str):
        self._opened = False
        self._archive = None
        self._path = pathlib.Path(fpath)
        self._pathfs = CoreFS(fpath)
        self._ext = self._pathfs.ext
        self.path_separator = '/'

        a = self._archive_cache.get(self._pathfs.path, False)
        if a:
            self._archive = a._archive
            self._opened = a._opened
            self.path_separator = self.path_separator
            self._archive_obj_ref_count.setdefault(self._archive, 0)
            self._archive_obj_ref_count[self._archive] += 1
        else:
            if not self._path.exists():
                raise exceptions.ArchiveExistError(str(self._path))
            if self._pathfs.ext not in CoreFS.archive_formats():
                raise exceptions.ArchiveUnsupportedError(str(self._path))

            try:
                with self._init.call_capture(self._ext, self._path) as plg:
                    self._archive = plg.first_or_none(True)

                if not self._archive:
                    raise exceptions.CoreError(
                        utils.this_function(),
                        "No valid archive handler found for this archive type: '{}'".format(
                            self._ext))

                with self._path_sep.call_capture(self._ext, self._archive) as plg:
                    p = plg.first_or_none(True)
                    self.path_separator = p if p else self.path_separator
            except BaseException:
                if self._archive:
                    self.close()
                raise

            self._archive_cache[self._pathfs.path] = self

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
            r = plg.first_or_none(True)
            if r is not None and r:
                raise exceptions.ArchiveCorruptError(str(self._path))

    def _normalize_filename(self, f):
        f = f.replace('/', self.path_separator)
        f = f.replace('\\', self.path_separator)
        return f

    def namelist(self):
        ""
        with self._namelist.call_capture(self._ext, self._archive) as plg:
            return plg.first_or_default()

    def is_dir(self, filename):
        """
        Checks if the provided name in the archive is a directory or not
        """
        filename = self._normalize_filename(filename)
        with self._is_dir.call_capture(self._ext, self._archive, filename) as plg:
            return plg.first_or_default()

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
            extract_path = plg.first_or_default()

        return pathlib.Path(extract_path)

    def extract_all(self, target):
        """
        Extracts all files to given path, and returns path
        """
        p = pathlib.Path(target)

        if not p.exists():
            raise exceptions.ArchiveExtractError("Target path does not exist: '{}'".format(str(p)))

        with self._extract_all.call_capture(self._ext, self._archive, p) as plg:
            extract_path = plg.first_or_default()

        return pathlib.Path(extract_path)

    def open(self, filename, *args, **kwargs):
        """
        Open file in archive, returns a file-like object.
        """
        filename = self._normalize_filename(filename)
        try:
            mode = args[0]
        except IndexError:
            mode = "r"
        args = list(args)
        if mode == "rb":
            args[0] = "r"
        with self._open.call_capture(self._ext, self._archive, filename, tuple(args), kwargs) as plg:
            r = plg.first_or_default()
            if not hasattr(r, 'read') or not hasattr(r, 'write'):
                raise exceptions.PluginHandlerError(plg.get_node(0), "Expected a file-like object from archive.open")
            self._opened = True
            return r

    def close(self, force=False):
        """
        Close archive, releases all open resources
        """
        refs = self._archive_obj_ref_count.get(self._archive, False)
        if not refs or force:
            with self._close.call_capture(self._ext, self._archive) as plg:
                plg.first_or_default()
            self._opened = False
            self._archive_obj_ref_count.pop(self._archive, False)
        else:
            self._archive_obj_ref_count[self._archive] += 1


class GalleryFS(CoreCommand):
    """
    Encapsulates an gallery object on the filesystem
    Args:
        path_or_dbitem: path to a valid gallery archive/folder or a :class:`.db.Gallery` database item
    """

    _evaluate: bool = CommandEntry("evaluate",
                                   CParam("path", str, "path to gallery"),
                                   __doc="""
                                Called to evaluate if path is a valid gallery or not
                                """,
                                   __doc_return="""
                                a bool indicating whether path is pointing to a valid gallery or not
                                """)

    _filter_pages: tuple = CommandEntry("filter_pages",
                                        CParam("pages", tuple, "a tuple of pages"),
                                        __doc="""
                                Called to filter out files not to be regarded as pages
                                """,
                                        __doc_return="""
                                a tuple of strings of all the pages that should NOT be included in the gallery
                                """)

    _parse_metadata_file: bool = CommandEntry("parse_metadata_file",
                                              CParam(
                                                  "path", str, "path to the gallery source, note that this can also be inside of an archive"),
                                              CParam("gallery", db.Gallery, "gallery db item"),
                                              __doc="""
                                Called to read and apply metadata from an identified metadata file accompanying a gallery
                                """,
                                              __doc_return="""
                                a bool indicating whether a file was identified and data was applied
                                """)

    def __init__(self, path_or_dbitem: typing.Union[db.Gallery, str, CoreFS, pathlib.Path]):
        assert isinstance(path_or_dbitem, (str, CoreFS, db.Gallery, pathlib.Path))
        self.path = None

        if isinstance(path_or_dbitem, db.Gallery):
            self.gallery = path_or_dbitem
        else:
            self.gallery = db.Gallery()
            self.path = CoreFS(path_or_dbitem)

        self.pages = {}  # number : db.Page
        self.metadata_from_file = False
        self.exists = None
        self._sources = None
        self._evaluated = None
        self._loaded_metadata = False
        self._loaded_pages = False

    def load_all(self, update=True, delete_existing=False, force=False):
        if self.evaluate(True):
            self.load_metadata(update=update, force=force)
            self.load_pages(delete_existing=delete_existing, force=force)

    def load_metadata(self, update=True, force=False):
        """
        """
        if self._loaded_metadata and not force:
            return
        sources = self.get_sources(only_single=True)
        sess = constants.db_session()
        with sess.no_autoflush:
            if not update and self.gallery.id:
                self.gallery = db.ensure_in_session(self.gallery)
            if not update:
                self.gallery.titles.clear()
            for p in sources:
                with self._parse_metadata_file.call(p, self.gallery) as plg:
                    # TODO: stop at first handler that returns true
                    self.metadata_from_file = any(plg.all(default=True))

                n = NameParser(os.path.split(p)[1])
                langs = []
                for l in n.extract_language():
                    langs.append(db.Language.as_unique(name=l, session=sess))

                lang = None
                if langs:
                    lang = langs[0]
                if lang and not self.gallery.language:
                    self.gallery.language = lang
                if not self.gallery.titles or not self.metadata_from_file:
                    for t in n.extract_title():
                        dbtitle = db.Title()
                        dbtitle.name = t
                        if lang:
                            dbtitle.language = lang
                        self.gallery.titles.append(dbtitle)
                circles = []
                for t in n.extract_circle():
                    circles.append(db.Circle.as_unique(name=t, session=sess))

                if not self.gallery.artists or not self.metadata_from_file:
                    for t in n.extract_artist():
                        dbartist = db.Artist.as_unique(name=t)
                        for an in dbartist.names:
                            if an.name == t:
                                dbartistname = an
                                break
                        else:
                            dbartistname = None

                        if dbartist not in self.gallery.artists:
                            self.gallery.artists.append(dbartist)

                        if lang and dbartistname and not dbartistname.language:
                            dbartistname.language = lang

                for a in self.gallery.artists:
                    if not a.circles or not self.metadata_from_file:
                        for c in circles:
                            if c not in a.circles:
                                a.circles.append(c)

                if not self.gallery.collections.count() or not self.metadata_from_file:
                    for col_name, cat_name in n.extract_collection():
                        dbcollection = db.Collection.as_unique(name=col_name, session=sess)
                        if cat_name:
                            dbcat = db.Category.as_unique(name=cat_name, session=sess)
                            dbcollection.category = dbcat
                        if dbcollection not in self.gallery.collections:
                            self.gallery.collections.append(dbcollection)

        self._loaded_metadata = True

    def load_pages(self, delete_existing=False, force=False):
        """
        """
        if self._loaded_pages and not force:
            return
        if self.evaluate(raise_error=True):
            sess = constants.db_session()
            with sess.no_autoflush:
                if delete_existing:
                    raise NotImplementedError
                    self.pages.clear()
                    if self.gallery.id:
                        self.gallery = db.ensure_in_session(self.gallery)
                        self.gallery.pages.delete()  # Can't call delete() when order_by has been applied

                n = 0
                for s in sorted(self.get_sources()):
                    fs = CoreFS(s)
                    c = tuple(x for x in fs.contents(corefs=False) if x.lower().endswith(CoreFS.image_formats()))
                    real_pages = OrderedSet(c)

                    with self._filter_pages.call(c) as plg:
                        for x in plg.all():
                            real_pages.difference_update(x)

                    for p in natsorted(real_pages):
                        n += 1
                        dbpage = db.Page()
                        dbpage.name = os.path.split(p)[1]
                        dbpage.path = p
                        dbpage.number = n
                        self.gallery.pages.append(dbpage, enable_count_cache=True)
                        self.pages[n] = p
                self.gallery.pages.reorder()
            self._loaded_pages = True

    def evaluate(self, raise_error=False):
        """
        """
        if self._evaluated is not None:
            return self._evaluated

        r = False

        for s in self.get_sources():
            sfs = CoreFS(s)
            if sfs.is_dir or (sfs.is_file and sfs.is_archive):
                r = True
                if sfs.is_dir and not [x for x in sfs.contents(corefs=False) if x.endswith(CoreFS.image_formats())]:
                    r = False

        self._evaluated = r
        return self._evaluated

    def get_gallery(self, load=True, update=True, check_exists=False):
        self.load_metadata(update=update)
        self.load_pages()
        if check_exists:
            self.check_exists()
        return self.gallery

    def get_sources(self, only_single=False):
        ""
        if only_single:
            if not self.gallery.single_source:
                raise NotImplementedError("Loading metadata for a gallery with multiple sources is not supported")

        if self.path:
            return (self.path.path,)
        if self._sources is not None:
            return self._sources

        paths = []
        if self.gallery.id:
            if self.pages:
                if self.gallery.single_source:
                    p_path = self.pages[1].path
                    paths.append(CoreFS(p_path).parent)
                else:
                    for p in self.pages.values():
                        p_path = CoreFS(p.path).parent
                        if p_path not in paths:
                            paths.append(p_path)
            else:
                paths = self.gallery.get_sources()

        return tuple(paths)

    def check_exists(self):
        if self.exists is not None:
            return self.exists
        v = False
        for p in self.get_sources():
            if db.Gallery.exists_by_path(p, obj=False):
                v = True
        self.exists = v
        return self.exists

    def add(self, view_id=constants.default_temp_view_id, skip_if_exists=False):
        """
        """
        assert isinstance(view_id, int)
        if not skip_if_exists or not self.check_exists():
            self.detach()
            constants.store.galleryfs_addition.get().setdefault(view_id, set()).add(self)

    def send_to_db(self, session=None):
        try:
            constants.store.galleryfs_addition.get().remove()
        except KeyError:
            pass

        session = session or constants.db_session()

        return session

    def detach(self):
        self.gallery = db.freeze_object(self.gallery)


class NameParser(CoreCommand):
    """
    Extract several components from a gallery name (usually a filename)

    Args:
        name: the string to parse

    """

    _extract_title: tuple = CommandEntry("extract_title",
                                         CParam(
                                             "name", str, "gallery name, usually a gallery's filename but with its extension removed"),
                                         __doc="""
                                Called to extract the title from ``name``
                                """,
                                         __doc_return="""
                                a tuple of strings of all the extracted titles
                                """)

    _extract_artist: tuple = CommandEntry("extract_artist",
                                          CParam(
                                              "name", str, "gallery name, usually a gallery's filename but with its extension removed"),
                                          __doc="""
                                Called to extract the artist from ``name``
                                """,
                                          __doc_return="""
                                a tuple of strings of all the extracted artists
                                """)

    _extract_collection: tuple = CommandEntry("extract_collection",
                                              CParam(
                                                  "name", str, "gallery name, usually a gallery's filename but with its extension removed"),
                                              __doc="""
                                Called to extract the convention/magazine from ``name``
                                """,
                                              __doc_return="""
                                a tuple of (collection_name, category_name) of all the extracted convention/magazines
                                """)

    _extract_language: tuple = CommandEntry("extract_language",
                                            CParam(
                                                "name", str, "gallery name, usually a gallery's filename but with its extension removed"),
                                            __doc="""
                                Called to extract the language from ``name``
                                """,
                                            __doc_return="""
                                a tuple of strings of all the extracted languages
                                """)

    _extract_circle: tuple = CommandEntry("extract_circle",
                                          CParam(
                                              "name", str, "gallery name, usually a gallery's filename but with its extension removed"),
                                          __doc="""
                                Called to extract the circle from ``name``
                                """,
                                          __doc_return="""
                                a tuple of strings of all the extracted circles
                                """)

    @_extract_title.default()
    def _extract_gallery_title(name):
        particles = list(regex.findall(r'((\[|{) *[^\]]+( +\S+)* *(\]|}))', name))  # everyting in brackets
        particles.extend(list(regex.findall(r"(\(C\d+\))", name, regex.IGNORECASE | regex.UNICODE)))  # Convention name

        for p in utils.regex_first_group(particles):
            name = name.replace(p, '')

        return tuple([utils.remove_multiple_spaces(name)])

    @_extract_language.default()
    def _extract_gallery_language(name):
        langs = []
        # everyting in brackets and colons; only singlewords
        particles = list(regex.findall(r'((?<=(\[|{|\()) *(\S+)* *(?=(\]|}|\))))', name))
        for p in reversed(utils.regex_first_group(particles)):
            try:
                l = langcodes.find(p)
                langs.append(l.autonym())
            except LookupError:
                pass

        return tuple(langs)

    @_extract_artist.default()
    def _extract_gallery_artist(name):
        artists = []
        for p in utils.regex_first_group(regex.findall(r"(\(C\d+\))", name, regex.IGNORECASE | regex.UNICODE)):
            name = name.replace(p, '')
        name = name.strip()
        r = regex.compile(r'((?<=(\[|{|\()) *[^\]]+( +\S+)* *(?=(\]|}|\))))')
        particles = utils.regex_first_group(r.findall(name))  # everyting in brackets and colons
        if particles:
            particles = particles[0]

            m = utils.regex_first_group(r.findall(particles))
            particles = m[0] if m else particles

            artists = [utils.remove_multiple_spaces(x) for x in particles.split(',')]

        return tuple(artists)

    @_extract_circle.default()
    def _extract_gallery_circle(name):
        circles = []
        for p in utils.regex_first_group(regex.findall(r"(\(C\d+\))", name, regex.IGNORECASE | regex.UNICODE)):
            name = name.replace(p, '')
        name = name.strip()
        r = regex.compile(r'((?<=(\[|{|\()) *[^\]]+( +\S+)* *(?=(\]|}|\))))')
        particles = utils.regex_first_group(r.findall(name))  # everyting in brackets and colons
        if particles:
            particles = particles[0]
            m = utils.regex_first_group(r.findall(particles))  # circle (artist)
            if m:
                for x in m:
                    ex = ('(' + x + ')')
                    if ex in particles:
                        particles = particles.replace(ex, '')
                    else:
                        particles = particles.replace(x, '')

                particles = particles.replace('[]', '')
                particles = particles.replace('()', '')
                particles = particles.replace('{}', '')
                particles = utils.remove_multiple_spaces(particles)
                circles.append(particles)

        return tuple(circles)

    @_extract_collection.default()
    def _extract_gallery_collection(name):
        category = ""
        col_name = ""

        class CType:
            comiket = 1
            gfm = 2

        for i, r in ((CType.comiket, r"(\(C\d+\))"),
                     (CType.gfm, r"(\(\s*(from)?\s*girls form vol\.?\s*\d*\s*\))")):
            m = regex.search(r, name, regex.IGNORECASE | regex.UNICODE)
            if m:
                if i == CType.comiket:
                    col_name = "Comiket " + "".join(x for x in m[0] if x.isdigit())
                    category = "Convention"
                elif i == CType.gfm:
                    d = "".join(x for x in m[0] if x.isdigit())
                    if len(d) == 1:
                        d = '0' + d
                    col_name = "Girls forM Vol. " + d
                    category = "Magazine"
                break

        return ((col_name, category),)

    def __init__(self, name: str):
        super().__init__()
        self.titles = tuple()
        self.artists = tuple()
        self.collections = tuple()
        self.languages = tuple()
        self.circles = tuple()

        fs = CoreFS(name)
        if fs.ext:
            self.name = name[:-len(fs.ext)]  # remove ext
        else:
            self.name = name
        self.name = utils.remove_multiple_spaces(self.name)

    def extract_title(self) -> typing.Tuple[str]:
        if self.titles:
            return self.titles

        with self._extract_title.call(self.name) as plg:
            ts = tuple()
            for t in plg.all(default=True):
                if t:
                    ts += t
            self.titles = tuple(x for x in ts if x)
        return self.titles

    def extract_artist(self) -> typing.Tuple[str]:
        if self.artists:
            return self.artists

        with self._extract_artist.call(self.name) as plg:
            ts = tuple()
            for t in plg.all(default=True):
                if t:
                    ts += t
            self.artists = tuple(x for x in ts if x)
        return self.artists

    def extract_circle(self) -> typing.Tuple[str]:
        if self.circles:
            return self.circles

        with self._extract_circle.call(self.name) as plg:
            ts = tuple()
            for t in plg.all(default=True):
                if t:
                    ts += t
            self.circles = tuple(x for x in ts if x)
        return self.circles

    def extract_collection(self) -> typing.Tuple[str]:
        if self.collections:
            return self.collections

        with self._extract_collection.call(self.name) as plg:
            ts = list()
            for t in plg.all(default=True):
                for x in t:
                    if isinstance(x, tuple) and len(x) == 2 and x[0]:
                        ts.append(x)
            self.collections = tuple(x for x in ts if x)
        return self.collections

    def extract_language(self) -> typing.Tuple[str]:
        if self.languages:
            return self.languages

        with self._extract_language.call(self.name) as plg:
            ts = tuple()
            for t in plg.all(default=True):
                if t:
                    ts += t
            self.languages = tuple(x for x in ts if x)
        return self.languages


class CacheCleaner(Command):
    """
    Clean the provided folder

    Args:
        cache_path: path to cache directory
        size: only clean if directory size exceeds this number in MB
        silent: ignore any errors

    Returns:
        bool indicating whether the folder was cleaned or not
    """

    def _calculate_size(self, path):
        "in bytes"
        total = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += self._calculate_size(entry.path)
        return total

    def _clean_contents(self, path, silent, size):

        # delete old files first
        files = list(sorted(os.scandir(path), key=lambda x: x.stat().st_ctime))
        for f in files[:int(len(files) / 2)]:
            try:
                if f.is_file():
                    os.unlink(f.path)
                elif f.is_dir():
                    shutil.rmtree(f.path)
            except Exception:
                if not silent:
                    raise

        while float(self._calculate_size(path)) > size:
            self._clean_contents(self, path, silent, size)

    def main(self, cache_path: typing.Union[CoreFS, str], size: float=0.0, silent: bool=False) -> bool:
        p = CoreFS(cache_path)
        size = float(size) * 1048576  # 1048576 bytes = 1 mb
        if p.exists and float(self._calculate_size(p.path)) > size:
            self._clean_contents(p.path, silent, size)
            return True
        return False
