"Contains classes/methods related to galleries"
import os
import scandir
import re

from happypanda.common import constants, utils
from happypanda.core import db, archive


class GalleryScan:
    """
    Scan filesystem for galleries
    Params:
        list_of_paths -- list of paths to scan for galleries
    Returns:
        Gallery objects
    """
    def __init__(self, list_of_paths):
        pass

    @staticmethod
    def fromPath(path, path_in_archive=''):
        """
        Add a single gallery from folder/archive
        Params:
            path -- a path to gallery folder/archive
            path_in_archive -- a path to gallery in archive
        Returns:
            Gallery object
        """
        ptype = utils.PathType.check(path)
        _, name = os.path.split(path)
        gallery = db.Gallery()
        gallery_info = {}

        if ptype == utils.PathType.Archive:
            pass
        elif ptype == utils.PathType.Directoy:
            gallery_info = GalleryScan.nameParser(name)

            dir_images = [x.path for x in scandir.scandir(path) if not x.is_dir() and x.name.endswith(constants.supported_images)]
            for n, x in enumerate(sorted(dir_images), 1):
                p = db.Page()
                p.name = os.path.abspath(x)
                p.number = n
                gallery.pages.append(p)

        for n in gallery_info:
            if n == 'title':
                t = db.Title()
                t.name = gallery_info['title']
                if gallery.language:
                    t.language = gallery.language
                gallery.titles.append(t)

            if n == 'artist':
                pass

            if n == 'language':
                pass

            if n == 'convention':
                pass

        return gallery

    @staticmethod
    def evaluatePath(path):
        """
        Evaluate path
        Params:
            path -- a path to gallery folder/archive
        Returns:
            bool
        """
        if os.path.exists(path):
            if utils.PathType.check(path) in (utils.PathType.Archive, utils.PathType.Directoy):
                return True
        return False

    @staticmethod
    def evaluateGallery(files):
        """
        Evaluate content to see if it's a valid gallery
        Params:
            files -- folder/archive contents
        Returns:
            bool
        """
        gallery_probability = len(files)
        for f in files:
            if not f.lower().endswith(constants.supported_images):
                gallery_probability -= 1
        if gallery_probability >= (len(files) * 0.8):
            return True
        return False

    @staticmethod
    def nameParser(name):
        """
        Parse gallery name, extracts title, artist, convention, etc.
        Params:
            name -- string to parse
        Returns:
            dictonary: {'title':"", 'artist':"", 'language':"", 'convention':""}
        """
        name = " ".join(name.split()) # remove unecessary whitespace
        if '/' in name:
            try:
                name = os.path.split(name)[1]
                if not name:
                    name = name
            except IndexError:
                pass

        for x in constants.supported_archives:
            if name.endswith(x):
                name = name[:-len(x)]

        dic = {'title':"", 'artist':"", 'language':"", 'convention':""}
        try:
            a = re.findall('((?<=\[) *[^\]]+( +\S+)* *(?=\]))', name)
            assert len(a) != 0
            artist = a[0][0].strip()
            dic['artist'] = artist

            try:
                assert a[1]
                lang = [] # TODO: retrieve languages from DB
                for x in a:
                    l = x[0].strip()
                    l = l.lower()
                    l = l.capitalize()
                    if l in lang:
                        dic['language'] = l
                        break
                else:
                    dic['language'] = 'English' # set default language
            except IndexError:
                dic['language'] = 'English' # set default language

            t = name
            for x in a:
                t = t.replace(x[0], '')

            t = t.replace('[]', '')
            final_title = t.strip()
            dic['title'] = final_title
        except AssertionError:
            dic['title'] = name

        return dic

class GalleryMonitor:
    pass