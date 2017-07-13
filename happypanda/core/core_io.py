import os
import re

from happypanda.common import constants, utils
from happypanda.core import plugins


class GalleryScan:
    """
    Scan filesystem for galleries
    Params:
        list_of_paths -- list of paths to scan for galleries
    Returns:
        Database Gallery objects
    """

    def __init__(self, list_of_paths):
        pass

    @staticmethod
    def from_path(path, path_in_archive=''):
        """
        Add a single gallery from folder/archive
        Params:
            path -- a path to gallery folder/archive
            path_in_archive -- a path to gallery in archive
        Returns:
            Gallery object or None
        """
        ptype = utils.PathType.check(path)
        contents = []
        gallery = None

        if ptype == utils.PathType.Archive:
            pass
        elif ptype == utils.PathType.Directoy:
            contents = [x.path for x in os.scandir(path) if not x.is_dir()] # noqa: F841

        #if GalleryScan.evaluate_gallery(contents):
        #    gfs = GalleryFS(path, path_in_archive)
        #    gfs.load()
        #    if constants.core_plugin:
        #        constants.core_plugin.instanced.on_gallery_from_path(gfs)
        #    gallery = gfs.get_gallery()

        return gallery

    @staticmethod
    def evaluate_path(path):
        """
        Evaluate path
        Params:
            path -- a path to gallery folder/archive
        Returns:
            bool
        """
        if os.path.exists(path):
            if utils.PathType.check(path) in (
                    utils.PathType.Archive, utils.PathType.Directoy):
                return True
        return False

    @staticmethod
    def evaluate_gallery(files):
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
    def name_parser(name):
        """
        Parse gallery name, extracts title, artist, convention, etc.
        Params:
            name -- string to parse
        Returns:
            dictonary: {'title':"", 'artist':"", 'language':"", 'convention':""}
        """
        if constants.core_plugin:
            with constants.core_plugin.instanced.on_gallery_name_parse as hook:
                r = hook(name)

                def plugin_assertion(x):
                    try:
                        if not isinstance(x['title'], str):
                            raise ValueError
                        if not isinstance(x['artist'], str):
                            raise ValueError
                        if not isinstance(x['language'], str):
                            raise ValueError
                        if not isinstance(x['convention'], str):
                            raise ValueError
                    except KeyError:
                        return False
                    except ValueError:
                        return False
                    return True
                dic = plugins.get_hook_return_type(r, dict, plugin_assertion)
                if dic:
                    return dic

        name = " ".join(name.split())  # remove unecessary whitespace
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

        dic = {'title': "", 'artist': "", 'language': "", 'convention': ""}
        try:
            a = re.findall('((?<=\[) *[^\]]+( +\S+)* *(?=\]))', name)
            assert len(a) != 0
            artist = a[0][0].strip()
            dic['artist'] = artist

            try:
                assert a[1]
                lang = []  # TODO: retrieve languages from DB
                for x in a:
                    l = x[0].strip()
                    l = l.lower()
                    l = l.capitalize()
                    if l in lang:
                        dic['language'] = l
                        break
                else:
                    dic['language'] = 'English'  # set default language
            except IndexError:
                dic['language'] = 'English'  # set default language

            t = name
            for x in a:
                t = t.replace(x[0], '')

            t = t.replace('[]', '')
            final_title = t.strip()
            dic['title'] = final_title
        except AssertionError:
            dic['title'] = name

        return dic
