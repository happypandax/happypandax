"""
.Gallery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import typing
import os
import subprocess
import math

from happypanda.common import utils, hlogger, config, exceptions, constants
from happypanda.core.command import (CommandEvent, CommandEntry, Command, AsyncCommand, CParam)
from happypanda.core.commands import database_cmd, io_cmd
from happypanda.interface import enums
from happypanda.core import db, async_utils

log = hlogger.Logger(constants.log_ns_command + __name__)


def _get_scan_options():
    return {
        config.skip_existing_galleries.fullname: config.skip_existing_galleries.value,
        config.scan_component_path.fullname: config.scan_component_path.value,
    }


class ScanGallery(AsyncCommand):
    """
    """

    _discover: tuple = CommandEntry("discover",
                                    CParam("path", str, "path to folder or archive"),
                                    CParam("options", dict, "a of options to be applied to the scan"),
                                    __doc="""
                            Called to find any valid galleries in the given path
                            """,
                                    __doc_return="""
                            a tuple of absolute paths or tuples to valid galleries found in the given directory/archive,
                            related galleries are put in their own tuple
                            """)

    _resolve: tuple = CommandEntry("resolve",
                                   CParam("path", str, "path to folder or archive"),
                                   CParam("options", dict, "a of options to be applied to the scan"),
                                   __doc="""
                            Called to resolve the user given scan component path
                            """,
                                   __doc_return="""
                            """)

    @_discover.default()
    def _find_galleries(path, options):
        path = io_cmd.CoreFS(path)
        archive_formats = io_cmd.CoreFS.archive_formats()
        found_galleries = []
        if path.is_archive or path.inside_archive:
            raise NotImplementedError
        else:
            contents = os.scandir(str(path))
            for p in contents:
                if p.is_file() and not p.path.endswith(archive_formats):
                    continue
                found_galleries.append(os.path.abspath(p.path))

        return tuple(found_galleries)

    #@classmethod
    #def _component_match(path, comps):
    #    item = {}

    #@_resolve.default()
    #def _resolve_scan(path, options):
    #    path = io_cmd.CoreFS(path)
    #    found_galleries = []
    #    scan_cmp = options.get(config.scan_component_path.fullname)
    #    components = scan_cmp.split('/')

    #    for con in path.contents(corfs=True):
    #        i_comps = list(components)

    #    return tuple(found_galleries)

    @async_utils.defer
    def _generate_gallery_fs(self, found_paths, options):
        paths_len = len(found_paths)
        galleries = []
        sess = constants.db_session()
        with db.no_autoflush(sess):
            for n, p in enumerate(found_paths, 1):
                self.next_progress(text=f"[{n}/{paths_len}] {p}")
                if options.get(config.skip_existing_galleries.fullname):
                    if db.Gallery.exists_by_path(p):
                        continue
                g = io_cmd.GalleryFS(p)
                if g.evaluate():
                    g.load_all()
                    self.set_progress(text=f"[{n}/{paths_len}] {g.path.path} .. OK")
                    galleries.append(g)
        return galleries

    def main(self, path: typing.Union[str, io_cmd.CoreFS], options: dict={},
             view_id: int=None, auto_add: bool=False) -> typing.List[io_cmd.GalleryFS]:
        fs = io_cmd.CoreFS(path)
        galleries = []
        self.set_progress(title=fs.path, text=fs.path, type_=enums.ProgressType.GalleryScan)
        self.set_max_progress(1)
        if fs.is_dir or fs.is_archive:
            scan_options = _get_scan_options()
            scan_options.update(options)
            found_paths = set()
            if fs.exists:
                with self._discover.call(fs.path, scan_options) as plg:
                    for p in plg.all(default=True):
                        [found_paths.add(os.path.normpath(x)) for x in p]

            paths_len = len(found_paths)
            log.d("Found", paths_len, "gallery candidates")

            self.set_max_progress(paths_len, add=True)
            view_id = view_id if view_id else constants.default_temp_view_id
            galleries = self._generate_gallery_fs(found_paths, scan_options).get()
            [x.add(view_id=view_id) for x in galleries]
            if auto_add:
                raise NotImplementedError
                #add_cmd = AddGallery()

        self.next_progress(text="")

        return galleries


class SimilarGallery(AsyncCommand):
    """
    Get a list of similar galleries to given gallery

    Args:
        gallery_or_id: a :class:`.db.Gallery` database item or an item id thereof

    Returns:
        a list of similar galleries sorted most to least
    """

    #calculate: int = CommandEntry("calculate", set, int)

    def main(self, gallery_or_id: db.Gallery) -> typing.List[db.Gallery]:
        gid = gallery_or_id.id if isinstance(gallery_or_id, db.Gallery) else gallery_or_id
        gid = str(gid)  # because JSON keys are str
        gl_data = {}
        all_gallery_tags = {}
        self.set_progress(type_=enums.ProgressType.Unknown)
        self.set_max_progress(1)
        idb = constants.internaldb
        if not constants.invalidator.similar_gallery:
            gl_data = idb.get(constants.internaldb.similar_gallery_calc.key, gl_data)
            all_gallery_tags = idb.get(constants.internaldb.similar_gallery_tags.key, all_gallery_tags)
        log.d("Cached gallery tags", len(all_gallery_tags))
        if gid not in gl_data:
            log.d("Similarity calculation not found in cache")
            gl_data.update(self._calculate(gallery_or_id, all_gallery_tags).get())
            idb = constants.internaldb
            idb[constants.internaldb.similar_gallery_calc.key] = gl_data
            idb[constants.internaldb.similar_gallery_tags.key] = all_gallery_tags
        self.next_progress()
        v = []
        if gid in gl_data:
            v = [int(x) for x in sorted(gl_data[gid], reverse=True, key=lambda x:gl_data[gid][x])]
        return v

    def __init__(self):
        super().__init__()

    def _get_set(self, tags):
        s = set()
        for ns, tags in tags.items():
            for t in tags:
                s.add("1-{}:{}".format(ns, t))
                # s.add("{}".format(ns.tag.name))
                # if not ns.namespace.name == constants.special_namespace:
                #    s.add("1-{}:{}".format(ns.namespace.name, ns.tag.name))
                #    s.add("2-{}:{}".format(ns.namespace.name, ns.tag.name))
        return s

    @async_utils.defer
    def _calculate(self, gallery_or_id, all_gallery_tags={}):
        assert isinstance(gallery_or_id, (str, int, db.Gallery))
        sess = constants.db_session()
        with db.no_autoflush(sess):
            data = {}
            g_id = gallery_or_id.id if isinstance(gallery_or_id, db.Gallery) else gallery_or_id
            g_id = str(g_id)  # because JSON keys are str
            tag_count = 0
            tag_count_minimum = 3
            if g_id in all_gallery_tags:
                g_tags = all_gallery_tags[g_id]
                for a, b in g_tags.items():
                    tag_count += len(b)
                self.set_max_progress(len(g_tags) + 3)
            else:
                if isinstance(gallery_or_id, db.Gallery):
                    g_tags = gallery_or_id
                else:
                    g_tags = database_cmd.GetModelItems().run(db.Taggable, join=db.Gallery.taggable,
                                                              filter=db.Gallery.id == int(g_id))
                    if g_tags:
                        g_tags = g_tags[0]
                    tag_count = g_tags.tags.count()
                    if tag_count > tag_count_minimum:
                        g_tags = g_tags.compact_tags(g_tags.tags.all())

            self.next_progress()
            if g_tags and tag_count > tag_count_minimum:
                log.d("Calculating similarity")
                g_tags = self._get_set(g_tags)
                data[g_id] = gl_data = {}
                update_dict = not all_gallery_tags
                max_prog = 3
                for t_id, t in all_gallery_tags.items() or constants.db_session().query(
                        db.Gallery.id, db.Taggable).join(db.Gallery.taggable):
                    t_id = str(t_id)
                    self.next_progress()
                    if update_dict:
                        all_gallery_tags[t_id] = t.compact_tags(t.tags.all())
                        max_prog += 1
                        self.set_max_progress(max_prog)
                    if t_id == g_id:
                        continue
                    t_tags = self._get_set(all_gallery_tags[t_id])
                    if (math.sqrt(len(g_tags)) * math.sqrt(len(t_tags))) != 0:
                        cos = len(g_tags & t_tags) / (math.sqrt(len(g_tags))) * math.sqrt(len(t_tags))
                    else:
                        cos = 0
                    if cos:
                        gl_data[t_id] = cos
                log.d("Finished calculating similarity")
            self.next_progress()

        return data


class OpenGallery(Command):
    """
    Open a gallery in an external viewer

    Args:
        gallery_or_id: a :class:`.db.Gallery` database item or an item id thereof
        number: page number
        args: arguments to pass to the external program

    Returns:
        bool indicating wether the gallery was successfully opened
    """

    _opened = CommandEvent("opened",
                           CParam("parent_path", str, "path to parent folder or archive"),
                           CParam("child_path", str, "path to opened file in folder or archive"),
                           CParam("gallery", db.Gallery, "database item object that was opened"),
                           CParam("number", int, "page number"),
                           __doc="""
                           Emitted when a gallery or page was successfully opened
                           """)

    _open: bool = CommandEntry("open",
                               CParam("parent_path", str, "path to parent folder or archive"),
                               CParam("child_path", str, "path to opened file in folder or archive"),
                               CParam("gallery", db.Gallery, "database item object that was opened"),
                               CParam("arguments", tuple, "a tuple of arguments to pass to the external program"),
                               __doc="""
                               Called to open the given file in an external program
                               """,
                               __doc_return="""
                               a bool indicating whether the file could be opened or not
                               """)
    _resolve: tuple = CommandEntry("resolve",
                                   CParam("gallery", db.Gallery, "database item object that was opened"),
                                   CParam("number", int, "page number"),
                                   __doc="""
                                   Called to resolve the parent (containing folder or archive) and child (the file, usually the first) paths
                                   """,
                                   __doc_return="""
                                   a tuple with two items, the parent (``str``) and child (``str``) paths
                                   """
                                   )

    def main(self, gallery_or_id: db.Gallery=None, number: int=None, args=tuple()) -> bool:
        assert isinstance(gallery_or_id, (db.Gallery, int))
        if isinstance(gallery_or_id, int):
            gallery = database_cmd.GetModelItems().run(db.Gallery, {gallery_or_id})
            if gallery:
                gallery = gallery[0]
        else:
            gallery = gallery_or_id
        self.gallery = gallery
        if number is None:
            number = 1
        opened = False
        if self.gallery.pages.count():
            with self._resolve.call(self.gallery, number) as plg:
                r = plg.first_or_default()
                if len(r) == 2:
                    self.path, self.first_file = r

            args = args if args else tuple(x.strip() for x in config.external_image_viewer_args.value.split())

            with self._open.call(self.path, self.first_file, self.gallery, args) as plg:
                try:
                    opened = plg.first_or_default()
                except OSError as e:
                    raise exceptions.CommandError(utils.this_command(self),
                                                  "Failed to open gallery with external viewer: {}".format(e.args[1]))

        else:
            log.w("Error opening gallery (), no page count".format(self.gallery.id))

        if opened:
            self._opened.emit(self.path, self.first_file, self.gallery, number)

        return opened

    def __init__(self):
        super().__init__()
        self.path = ""
        self.first_file = ""
        self.gallery = None

    @_open.default()
    def _open_gallery(parent, child, gallery, args):
        ex_path = config.external_image_viewer.value.strip()
        log.d("Opening gallery ({}):\n\tparent:{}\n\tchild:{}".format(gallery.id, parent, child))
        log.d("External viewer:", ex_path)
        log.d("External args:", args)
        opened = False
        path = parent
        if child and config.send_path_to_first_file.value:
            path = child

        if ex_path:
            subprocess.Popen((ex_path, path, *args))
            opened = True
        else:
            io_cmd.CoreFS.open_with_default(path)
            opened = True

        return opened

    @_resolve.default()
    def _resolve_gallery(gallery, number):
        parent = ""
        child = ""
        if gallery.single_source:
            if gallery.pages.count():
                # TODO: when number 1 doesnt exist?
                first_page = gallery.pages.filter(db.Page.number == number).first()
                if first_page:
                    if first_page.in_archive:
                        p = io_cmd.CoreFS(first_page.path)
                        parent = p.archive_path
                        child = p.path
                    else:
                        child = first_page.path
                        parent = os.path.split(first_page.path)[0]
        else:
            raise NotImplementedError

        return parent, child
