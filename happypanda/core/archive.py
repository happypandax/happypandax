"Contains classes and methods to manage archive files"
import zipfile
import rarfile
import os
import uuid

from happypanda.common import exceptions, constants, hlogger

log = hlogger.Logger(__name__)


class ArchiveFile():
    """
    Work with archive files, raises exception if instance fails.
    namelist -> returns a list with all files in archive
    extract <- Extracts one specific file to given path
    open -> open the given file in archive, returns bytes
    close -> close archive
    """
    ZIP = '.zip'
    RAR = '.rar'

    SUPPORTED_FORMATS = (ZIP, RAR)

    def __init__(self, filepath):
        assert isinstance(filepath, str), "Filepath must be string"
        self.archive_type = 0
        self.filepath = filepath = filepath.lower()
        try:
            if filepath.lower().endswith(self.SUPPORTED_FORMATS):
                if filepath.endswith(self.ZIP):
                    self.archive = zipfile.ZipFile(os.path.normcase(filepath))
                    b_f = self.archive.testzip()
                    self.archive_type = self.ZIP
                elif filepath.endswith(self.RAR):
                    self.archive = rarfile.RarFile(os.path.normcase(filepath))
                    b_f = self.archive.testrar()
                    self.archive_type = self.RAR

                # test for corruption
                if b_f:
                    # log bad file
                    raise exceptions.ArchiveCorruptError(filepath)
            else:
                # log unsupprtoed
                raise exceptions.ArchiveUnsupportedError(filepath)
        except (zipfile.error, rarfile.Error) as e:
            # log error
            raise exceptions.ArchiveCreateError(filepath, e)

    def namelist(self):
        filelist = self.archive.namelist()
        return filelist

    def is_dir(self, name):
        """
        Checks if the provided name in the archive is a directory or not
        """
        if not name:
            return False
        if name not in self.namelist():
            log.e('File {} not found in archive'.format(name))
            raise exceptions.ArchiveFileNotFoundError(name, self.filepath)
        if self.archive_type == self.ZIP:
            if name.endswith('/'):
                return True
        elif self.archive_type == self.RAR:
            info = self.archive.getinfo(name)
            return info.isdir()
        return False

    def dir_list(self, only_top_level=False):
        """
        Returns a list of all directories found recursively. For directories not in toplevel
        a path in the archive to the diretory will be returned.
        """

        if only_top_level:
            if self.archive_type == self.ZIP:
                return [x for x in self.namelist() if x.endswith('/')
                        and x.count('/') == 1]
            elif self.archive_type == self.RAR:
                potential_dirs = [
                    x for x in self.namelist() if x.count('/') == 0]
                return [
                    x.filename for x in [
                        self.archive.getinfo(y) for y in potential_dirs] if x.isdir()]
        else:
            if self.archive_type == self.ZIP:
                return [x for x in self.namelist() if x.endswith('/')
                        and x.count('/') >= 1]
            elif self.archive_type == self.RAR:
                return [x.filename for x in self.archive.infolist()
                        if x.isdir()]

    def dir_contents(self, dir_name):
        """
        Returns a list of contents in the directory
        An empty string will return the contents of the top folder
        """
        if dir_name and dir_name not in self.namelist():
            log.e('Directory {} not found in archive'.format(dir_name))
            raise exceptions.ArchiveFileNotFoundError
        if not dir_name:
            if self.archive_type == self.ZIP:
                con = [x for x in self.namelist() if x.count('/') == 0 or
                       (x.count('/') == 1 and x.endswith('/'))]
            elif self.archive_type == self.RAR:
                con = [x for x in self.namelist() if x.count('/') == 0]
            return con
        if self.archive_type == self.ZIP:
            dir_con_start = [
                x for x in self.namelist() if x.startswith(dir_name)]
            return [x for x in dir_con_start if x.count('/') == dir_name.count(
                '/') or (x.count('/') == 1 + dir_name.count('/') and x.endswith('/'))]
        elif self.archive_type == self.RAR:
            return [x for x in self.namelist() if x.startswith(dir_name) and
                    x.count('/') == 1 + dir_name.count('/')]
        return []

    def extract(self, file_to_ext, dir=None):
        """
        Extracts one file from archive to given path
        Creates a temp_dir if path is not specified
        Returns path to the extracted file
        """
        if not dir:
            dir = os.path.join(
                constants.dir_temp, str(
                    uuid.uuid4()))  # TODO: use temp facilities
            os.mkdir(dir)

        if not file_to_ext:
            return self.extract_all(dir)
        else:
            if self.archive_type == self.zip:
                membs = []
                for name in self.namelist():
                    if name.startswith(file_to_ext) and name != file_to_ext:
                        membs.append(name)
                temp_p = self.archive.extract(file_to_ext, dir)
                for m in membs:
                    self.archive.extract(m, dir)
            elif self.archive_type == self.rar:
                temp_p = os.path.join(dir, file_to_ext)
                self.archive.extract(file_to_ext, dir)
            return temp_p

    def extract_all(self, path=None, member=None):
        """
        Extracts all files to given path, and returns path
        If path is not specified, a temp dir will be created
        """
        if not path:
            path = os.path.join(constants.dir_temp, str(uuid.uuid4()))  # TODO: use temp facilities
            os.mkdir(path)
        if member:
            self.archive.extractall(path, member)
        self.archive.extractall(path)
        return path

    def open(self, file_to_open, fp=False):
        """
        Returns bytes. If fp set to true, returns file-like object.
        """
        if fp:
            return self.archive.open(file_to_open)
        else:
            return self.archive.open(file_to_open).read()

    def close(self):
        self.archive.close()
