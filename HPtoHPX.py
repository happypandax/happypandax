#!/usr/bin/python3
# flake8: noqa
import sys
import os
import sqlite3
import copy
import arrow
import argparse
import rarfile
import time
import multiprocessing
import threading
import queue
import codecs
import regex
import pathlib

from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from multiprocessing import Process, Queue, Pipe
from natsort import natsorted

from happypanda.core import db, plugins
from happypanda.core.commands import io_cmd
from happypanda.common import constants, config, utils
_print = print


def safeprint(*s):
    try:
        _print(*s)
    except UnicodeEncodeError:
        _print(*[x.encode(errors="ignore") for x in s])


print = safeprint

GALLERY_LISTS = []
pages_out = queue.Queue()


def chapter_map(row, chapter):
    assert isinstance(chapter, Chapter)
    chapter.title = row['chapter_title']
    chapter.path = bytes.decode(row['chapter_path'])
    chapter.in_archive = row['in_archive']
    chapter.pages = row['pages']
    return chapter


def gallery_map(row, gallery, chapters=True, tags=True, hashes=True):
    gallery.title = row['title']
    gallery.artist = row['artist']
    gallery.profile = bytes.decode(row['profile'])
    gallery.path = bytes.decode(row['series_path'])
    gallery.is_archive = row['is_archive']
    try:
        gallery.path_in_archive = bytes.decode(row['path_in_archive'])
    except TypeError:
        pass
    gallery.info = row['info']
    gallery.language = row['language']
    gallery.rating = row['rating']
    gallery.status = row['status']
    gallery.type = row['type']
    gallery.fav = row['fav']

    def convert_date(date_str):
        # 2015-10-25 21:44:38
        if date_str and date_str != 'None':
            return arrow.get(date_str, "YYYY-MM-DD HH:mm:ss")

    gallery.pub_date = convert_date(row['pub_date'])
    gallery.last_read = convert_date(row['last_read'])
    gallery.date_added = convert_date(row['date_added'])
    gallery.times_read = row['times_read']
    gallery._db_v = row['db_v']
    gallery.exed = row['exed']
    gallery.view = row['view']
    try:
        gallery.link = bytes.decode(row['link'])
    except TypeError:
        gallery.link = row['link']

    if chapters:
        gallery.chapters = ChapterDB.get_chapters_for_gallery(gallery.id)

    if tags:
        gallery.tags = TagDB.get_gallery_tags(gallery.id)

    if hashes:
        gallery.hashes = HashDB.get_gallery_hashes(gallery.id)

    gallery.set_defaults()
    return gallery


class DBBase:
    "The base DB class. _DB_CONN should be set at runtime on startup"
    _DB_CONN = None
    _AUTO_COMMIT = True
    _STATE = {'active': False}

    def __init__(self, **kwargs):
        pass

    @classmethod
    def begin(cls):
        "Useful when modifying for a large amount of data"
        if not cls._STATE['active']:
            cls._AUTO_COMMIT = False
            cls.execute(cls, "BEGIN TRANSACTION")
            cls._STATE['active'] = True
        #print("STARTED DB OPTIMIZATION")

    @classmethod
    def end(cls):
        "Called to commit and end transaction"
        if cls._STATE['active']:
            try:
                cls.execute(cls, "COMMIT")
            except sqlite3.OperationalError:
                pass
            cls._AUTO_COMMIT = True
            cls._STATE['active'] = False
        #print("ENDED DB OPTIMIZATION")

    def execute(self, *args):
        "Same as cursor.execute"
        if self._AUTO_COMMIT:
            try:
                with self._DB_CONN:
                    return self._DB_CONN.execute(*args)
            except sqlite3.InterfaceError:
                return self._DB_CONN.execute(*args)

        else:
            return self._DB_CONN.execute(*args)

    def commit(self):
        self._DB_CONN.commit()

    @classmethod
    def analyze(cls):
        cls._DB_CONN.execute('ANALYZE')

    @classmethod
    def close(cls):
        cls._DB_CONN.close()


class GalleryDB(DBBase):
    """
    Provides the following s methods:
        rebuild_thumb -> Rebuilds gallery thumbnail
        rebuild_galleries -> Rebuilds the galleries in DB
        modify_gallery -> Modifies gallery with given gallery id
        get_all_gallery -> returns a list of all gallery (<Gallery> class) currently in DB
        get_gallery_by_path -> Returns gallery with given path
        get_gallery_by_id -> Returns gallery with given id
        add_gallery -> adds gallery into db
        set_gallery_title -> changes gallery title
        gallery_count -> returns amount of gallery (can be used for indexing)
        del_gallery -> deletes the gallery with the given id recursively
        check_exists -> Checks if provided string exists
        clear_thumb -> Deletes a thumbnail
        clear_thumb_dir -> Dletes everything in the thumbnail directory
    """

    def __init__(self):
        raise Exception("GalleryDB should not be instantiated")

    @classmethod
    def get_all_gallery(cls, chapters=True, tags=True, hashes=True):
        """
        Careful, might crash with very large libraries i think...
        Returns a list of all galleries (<Gallery> class) currently in DB
        """
        cursor = cls.execute(cls, 'SELECT * FROM series')
        all_gallery = cursor.fetchall()
        return GalleryDB.gen_galleries(all_gallery, chapters, tags, hashes)

    @staticmethod
    def gen_galleries(gallery_dict, chapters=True, tags=True, hashes=True):
        """
        Map galleries fetched from DB
        """
        gallery_list = []
        for gallery_row in gallery_dict:
            gallery = Gallery()
            gallery.id = gallery_row['series_id']
            gallery = gallery_map(gallery_row, gallery, chapters, tags, hashes)
            if not os.path.exists(gallery.path):
                gallery.dead_link = True
            ListDB.query_gallery(gallery)
            gallery_list.append(gallery)

        return gallery_list

    @classmethod
    def gallery_count(cls):
        """
        Returns the amount of galleries in db.
        """
        cursor = cls.execute(cls, "SELECT count(*) AS 'size' FROM series")
        return cursor.fetchone()['size']


class ChapterDB(DBBase):
    """
    Provides the following database methods:
        update_chapter -> Updates an existing chapter in DB
        add_chapter -> adds chapter into db
        add_chapter_raw -> links chapter to the given seires id, and adds into db
        get_chapters_for_gallery -> returns a dict with chapters linked to the given series_id
        get_chapter-> returns a dict with chapter matching the given chapter_number
        get_chapter_id -> returns id of the chapter number
        chapter_size -> returns amount of manga (can be used for indexing)
        del_all_chapters <- Deletes all chapters with the given series_id
        del_chapter <- Deletes chapter with the given number from gallery
    """

    def __init__(self):
        raise Exception("ChapterDB should not be instantiated")

    @classmethod
    def get_chapters_for_gallery(cls, series_id):
        """
        Returns a ChaptersContainer of chapters matching the received series_id
        """
        assert isinstance(series_id, int), "Please provide a valid gallery ID"
        cursor = cls.execute(cls, 'SELECT * FROM chapters WHERE series_id=?', (series_id,))
        rows = cursor.fetchall()
        chapters = ChaptersContainer()

        for row in rows:
            chap = chapters.create_chapter(row['chapter_number'])
            chapter_map(row, chap)
        return chapters


class HashDB(DBBase):
    """
    Contains the following methods:

    find_gallery -> returns galleries which matches the given list of hashes
    get_gallery_hashes -> returns all hashes with the given gallery id in a list
    get_gallery_hash -> returns hash of chapter specified. If page is specified, returns hash of chapter page
    gen_gallery_hashes <- generates hashes for gallery's chapters and inserts them to db
    rebuild_gallery_hashes <- inserts hashes into DB only if it doesnt already exist
    """
    @classmethod
    def get_gallery_hashes(cls, gallery_id):
        "Returns all hashes with the given gallery id in a list"
        cursor = cls.execute(cls, 'SELECT hash FROM hashes WHERE series_id=?',
                             (gallery_id,))
        hashes = []
        try:
            for row in cursor.fetchall():
                hashes.append(row['hash'])
        except IndexError:
            return []
        return hashes


class TagDB(DBBase):
    """
    Tags are returned in a dict where {"namespace":["tag1","tag2"]}
    The namespace "default" will be used for tags without namespaces.

    Provides the following methods:
    del_tags <- Deletes the tags with corresponding tag_ids from DB
    del_gallery_tags_mapping <- Deletes the tags and gallery mappings with corresponding series_ids from DB
    get_gallery_tags -> Returns all tags and namespaces found for the given series_id;
    get_tag_gallery -> Returns all galleries with the given tag
    get_ns_tags -> "Returns a dict with namespace as key and list of tags as value"
    get_ns_tags_to_gallery -> Returns all galleries linked to the namespace tags. Receives a dict like this: {"namespace":["tag1","tag2"]}
    get_tags_from_namespace -> Returns all galleries linked to the namespace
    add_tags <- Adds the given dict_of_tags to the given series_id
    modify_tags <- Modifies the given tags
    get_all_tags -> Returns all tags in database
    get_all_ns -> Returns all namespaces in database
    """

    def __init__(self):
        raise Exception("TagsDB should not be instantiated")

    @classmethod
    def get_gallery_tags(cls, series_id):
        "Returns all tags and namespaces found for the given series_id"
        if not isinstance(series_id, int):
            return {}
        cursor = cls.execute(cls, 'SELECT tags_mappings_id FROM series_tags_map WHERE series_id=?',
                             (series_id,))
        tags = {}
        result = cursor.fetchall()
        for tag_map_row in result:  # iterate all tag_mappings_ids
            try:
                if not tag_map_row:
                    continue
                # get tag and namespace
                c = cls.execute(cls, 'SELECT namespace_id, tag_id FROM tags_mappings WHERE tags_mappings_id=?',
                                (tag_map_row['tags_mappings_id'],))
                for row in c.fetchall():  # iterate all rows
                    # get namespace
                    c = cls.execute(cls, 'SELECT namespace FROM namespaces WHERE namespace_id=?',
                                    (row['namespace_id'],))
                    try:
                        namespace = c.fetchone()['namespace']
                    except TypeError:
                        continue

                    # get tag
                    c = cls.execute(cls, 'SELECT tag FROM tags WHERE tag_id=?', (row['tag_id'],))
                    try:
                        tag = c.fetchone()['tag']
                    except TypeError:
                        continue

                    # add them to dict
                    if namespace not in tags:
                        tags[namespace] = [tag]
                    else:
                        # namespace already exists in dict
                        tags[namespace].append(tag)
            except IndexError:
                continue
        return tags


class ListDB(DBBase):
    """
    """

    @classmethod
    def init_lists(cls):
        "Creates and returns lists fetched from DB"
        lists = []
        c = cls.execute(cls, 'SELECT * FROM list')
        list_rows = c.fetchall()
        for l_row in list_rows:
            l = GalleryList(l_row['list_name'], filter=l_row['list_filter'], id=l_row['list_id'])
            if l_row['type'] == GalleryList.COLLECTION:
                l.type = GalleryList.COLLECTION
            elif l_row['type'] == GalleryList.REGULAR:
                l.type = GalleryList.REGULAR
            profile = l_row['profile']
            if profile:
                l.profile = bytes.decode(profile)
            l.enforce = bool(l_row['enforce'])
            l.regex = bool(l_row['regex'])
            l.case = bool(l_row['l_case'])
            l.strict = bool(l_row['strict'])
            lists.append(l)
            GALLERY_LISTS.append(l)

        return lists

    @classmethod
    def query_gallery(cls, gallery):
        "Maps gallery to the correct lists"

        c = cls.execute(cls, 'SELECT list_id FROM series_list_map WHERE series_id=?', (gallery.id,))
        list_rows = [x['list_id'] for x in c.fetchall()]
        for l in GALLERY_LISTS:
            if l._id in list_rows:
                l.add_gallery(gallery, False, _check_filter=False)


class GalleryList:
    """
    Provides access to lists..
    methods:
    - add_gallery <- adds a gallery of Gallery class to list
    - remove_gallery <- removes galleries matching the provided gallery id
    - clear <- removes all galleries from the list
    - galleries -> returns a list with all galleries in list
    - scan <- scans for galleries matching the listfilter and adds them to gallery
    """
    # types
    REGULAR, COLLECTION = range(2)

    def __init__(self, name, list_of_galleries=[], filter=None, id=None, _db=True):
        self._id = id  # shouldnt ever be touched
        self.name = name
        self.profile = ''
        self.type = self.REGULAR
        self.filter = filter
        self.enforce = False
        self.regex = False
        self.case = False
        self.strict = False
        self._galleries = set()
        self._ids_chache = []
        self._scanning = False

    def add_gallery(self, gallery_or_list_of, _db=True, _check_filter=True):
        "add_gallery <- adds a gallery of Gallery class to list"
        assert isinstance(gallery_or_list_of, (Gallery, list))
        if isinstance(gallery_or_list_of, Gallery):
            gallery_or_list_of = [gallery_or_list_of]
        if _check_filter and self.filter and self.enforce:
            execute(self.scan, True, gallery_or_list_of)
            return
        new_galleries = []
        for gallery in gallery_or_list_of:
            self._galleries.add(gallery)
            new_galleries.append(gallery)
            self._ids_chache.append(gallery.id)
            # uses timsort algorithm so it's ok
            self._ids_chache.sort()

    def galleries(self):
        "returns a list with all galleries in list"
        return list(self._galleries)


class Gallery:
    """
    Base class for a gallery.
    Available data:
    id -> Not to be editied. Do not touch.
    title <- [list of titles] or str
    profile <- path to thumbnail
    path <- path to gallery
    artist <- str
    chapters <- {<number>:<path>}
    chapter_size <- int of number of chapters
    info <- str
    fav <- int (1 for true 0 for false)
    rating <- float
    type <- str (Manga? Doujin? Other?)
    language <- str
    status <- "unknown", "completed" or "ongoing"
    tags <- list of str
    pub_date <- date
    date_added <- date, will be defaulted to today if not specified
    last_read <- timestamp (e.g. time.time())
    times_read <- an integer telling us how many times the gallery has been opened
    hashes <- a list of hashes of the gallery's chapters
    exed <- indicator on if gallery metadata has been fetched
    valid <- a bool indicating the validity of the gallery

    Takes ownership of ChaptersContainer
    """

    def __init__(self):

        self.id = None  # Will be defaulted.
        self.title = ""
        self.profile = ""
        self._path = ""
        self.path_in_archive = ""
        self.is_archive = 0
        self.artist = ""
        self._chapters = ChaptersContainer(self)
        self.info = ""
        self.fav = 0
        self.rating = 0
        self.type = ""
        self.link = ""
        self.language = ""
        self.status = ""
        self.tags = {}
        self.pub_date = None
        self.date_added = arrow.now()
        self.last_read = None
        self.times_read = 0
        self.valid = False
        self._db_v = None
        self.hashes = []
        self.exed = 0
        self.file_type = "folder"
        self.view = 0

        self._grid_visible = False
        self._list_view_selected = False
        self._profile_qimage = {}
        self._profile_load_status = {}
        self.dead_link = False
        self.state = 0

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, n_p):
        self._path = n_p
        _, ext = os.path.splitext(n_p)
        if ext:
            self.file_type = ext[1:].lower()  # remove dot

    def set_defaults(self):
        pass

    @property
    def chapters(self):
        return self._chapters

    @chapters.setter
    def chapters(self, chp_cont):
        assert isinstance(chp_cont, ChaptersContainer)
        chp_cont.set_parent(self)
        self._chapters = chp_cont

    def __contains__(self, key):
        assert isinstance(key, Chapter), "Can only check for chapters in gallery"
        return self.chapters.__contains__(key)

    def __lt__(self, other):
        return self.id < other.id

    def __str__(self):
        s = ""
        for x in sorted(self.__dict__):
            s += "{:>20}: {:>15}\n".format(x, str(self.__dict__[x]))
        return s


class Chapter:
    """
    Base class for a chapter
    Contains following attributes:
    parent -> The ChapterContainer it belongs in
    gallery -> The Gallery it belongs to
    title -> title of chapter
    path -> path to chapter
    number -> chapter number
    pages -> chapter pages
    in_archive -> 1 if the chapter path is in an archive else 0
    """

    def __init__(self, parent, gallery, number=0, path='', pages=0, in_archive=0, title=''):
        self.parent = parent
        self.gallery = gallery
        self.title = title
        self.path = path
        self.number = number
        self.pages = pages
        self.in_archive = in_archive

    def __lt__(self, other):
        return self.number < other.number

    def __str__(self):
        s = """
        Chapter: {}
        Title: {}
        Path: {}
        Pages: {}
        in_archive: {}
        """.format(self.number, self.title, self.path, self.pages, self.in_archive)
        return s

    @property
    def next_chapter(self):
        try:
            return self.parent[self.number + 1]
        except KeyError:
            return None

    @property
    def previous_chapter(self):
        try:
            return self.parent[self.number - 1]
        except KeyError:
            return None


class ChaptersContainer:
    """
    A container for chapters.
    Acts like a list/dict of chapters.

    Iterable returns a ordered list of chapters
    Sets to gallery.chapters
    """

    def __init__(self, gallery=None):
        self.parent = None
        self._data = {}

        if gallery:
            gallery.chapters = self

    def set_parent(self, gallery):
        assert isinstance(gallery, (Gallery, None))
        self.parent = gallery
        for n in self._data:
            chap = self._data[n]
            chap.gallery = gallery

    def add_chapter(self, chp, overwrite=True, db=False):
        "Add a chapter of Chapter class to this container"
        assert isinstance(chp, Chapter), "Chapter must be an instantiated Chapter class"

        if not overwrite:
            try:
                _ = self._data[chp.number]  # noqa: F841
                raise Exception
            except KeyError:
                pass
        chp.gallery = self.parent
        chp.parent = self
        self[chp.number] = chp

        if db:
            # TODO: implement this
            pass

    def create_chapter(self, number=None):
        """
        Creates Chapter class with the next chapter number or passed number arg and adds to container
        The chapter will be returned
        """
        if number:
            chp = Chapter(self, self.parent, number=number)
            self[number] = chp
        else:
            next_number = 0
            for n in list(self._data.keys()):
                if n > next_number:
                    next_number = n
                else:
                    next_number += 1
            chp = Chapter(self, self.parent, number=next_number)
            self[next_number] = chp
        return chp

    def pages(self):
        p = 0
        for c in self:
            p += c.pages
        return p

    def get_chapter(self, number):
        return self[number]

    def get_all_chapters(self):
        return list(self._data.values())

    def count(self):
        return len(self)

    def pop(self, key, default=None):
        return self._data.pop(key, default)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        assert isinstance(key, int), "Key must be a chapter number"
        assert isinstance(value, Chapter), "Value must be an instantiated Chapter class"

        if value.gallery != self.parent:
            raise app_constants.ChapterWrongParentGallery
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter([self[c] for c in sorted(self._data.keys())])

    def __bool__(self):
        return bool(self._data)

    def __str__(self):
        s = ""
        for c in self:
            s += '\n' + '{}'.format(c)
        if not s:
            return '{}'
        return s

    def __contains__(self, key):
        if key.gallery == self.parent and key in [self.data[c] for c in self._data]:
            return True
        return False


def split(a, n):
    n = min(n, len(a))
    if not n:
        return [a]
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help="Print out a lot of useful information")
    parser.add_argument('source', help="Path to old HP database")
    parser.add_argument('destination', help="Desired path to new HPX database")
    parser.add_argument('-r', '--rar', help="Path to unrar tool", default=config.unrar_tool_path.value)
    parser.add_argument('-l', '--limit', type=int, default=-
                        1, help="Limit the amount of galleries being added (inclusive)")
    parser.add_argument(
        '-o',
        '--offset',
        type=int,
        default=0,
        help="Offset the amount of galleries being added (exclusive)")
    parser.add_argument('-p', '--process', type=int, default=3, help="Amount of processes allowed to spawn")
    parser.add_argument(
        '-a',
        '--skip-archive',
        action='store_true',
        help="Skip generating pages for galleries in archive files (it might take too long)")
    parser.add_argument(
        '-d',
        '--delete-target',
        action='store_true',
        help="Delete target database if it already exists")
    args = parser.parse_args(args)
    return args


def _page_gen(items):
    while items:
        item = items.pop()
        gallery, ch_inarchive, ch_path, path, g_path = item
        pages = []
        page_hash = None
        img_formats = io_cmd.CoreFS.image_formats()
        try:
            if ch_inarchive:
                page_hash = (g_path, ch_path)
                afs = None
                try:
                    contents = []
                    if ch_path:
                        afs = io_cmd.Archive(path)
                        contents = [os.path.join(path, x)
                                    for x in afs.namelist() if x.startswith(ch_path)]
                    else:
                        afs = io_cmd.CoreFS(path)
                        contents = afs.contents(corefs=False)
                    n = 1
                    for c in natsorted(contents):
                        if c.endswith(img_formats):
                            c = str(pathlib.Path(c))
                            pages.append((os.path.split(c)[1], c, n, True))
                            n += 1
                finally:
                    if afs:
                        afs.close()
            else:
                page_hash = (ch_path,)
                dir_images = [
                    x.path for x in os.scandir(ch_path) if not x.is_dir() and x.name.endswith(
                        img_formats)]
                for n, x in enumerate(natsorted(dir_images), 1):
                    x = io_cmd.CoreFS(x)
                    pages.append((x.name, x.path, n, False))
        except NotImplementedError:
            pass
        except rarfile.RarCannotExec:
            print("RAR file not supported, skipping: {}".format(g_path))
        except BaseException as e:
            print("An unknown error occured, skipping: {}\n\t{}".format(g_path, e))

        yield (page_hash, gallery, pages)


def page_generate(rar_p, args, out_pipe):
    rarfile.UNRAR_TOOL = rar_p
    item_id, items = args
    stuff_to_send = []
    items_len = len(items)
    for n_item, x in enumerate(_page_gen(items), 1):
        stuff_to_send.append(x)
        if len(stuff_to_send) > 5 or n_item == items_len:
            out_pipe.send(stuff_to_send.copy())
            stuff_to_send.clear()
    out_pipe.send(item_id)


def process_pipes(out_queue, out_pipe):
    while True:
        try:
            out_queue.put(out_pipe.recv())
        except (EOFError, AssertionError):
            break


def extract_collection(title):
    """
    Extract Comic Market
    """
    title = title.strip()
    category = ""
    col_name = ""

    class CType:
        comiket = 1
        gfm = 2

    for i, r in ((CType.comiket, r"(\(C\d+\))"),
                 (CType.gfm, r"(\(\s*(from)?\s*girls form vol\.?\s*\d*\s*\))")):
        m = regex.search(r, title, regex.IGNORECASE | regex.UNICODE)
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
            title = " ".join(title.replace(m[0], '').strip().split())
            break

    return col_name, title, category


def main(args=sys.argv[1:]):
    try:

        args = parse_args(args)

        AMOUNT_OF_TASKS = args.process if args.process > 0 else 1
        rarfile.UNRAR_TOOL = args.rar

        src = args.source
        dst = args.destination
        print("Source: ", src)
        print("Destination: ", dst)

        try:
            is_rfc = os.path.exists(dst)
        except BaseException:
            is_rfc = None
        is_rfc = False if is_rfc else any(dst.lower().startswith(x)
                                          for x in ('postgres:', 'mysql+pymysql:', 'sqlite:', 'mysql:'))

        if dst.startswith('mysql://'):
            dst = dst.replace('mysql://', 'mysql+pymysql://')
        is_new_db = False
        if (is_rfc and database_exists(dst)) or os.path.exists(dst):
            if args.delete_target:
                print("Deleting existing target database")
                if not is_rfc:
                    os.unlink(dst)
                else:
                    drop_database(dst)
                is_new_db = True
            else:
                print("Warning: destination database already exists, existing galleries will not be added")
        elif not is_rfc:
            is_new_db = True
            head, _ = os.path.split(dst)
            if head:
                os.makedirs(head, exist_ok=True)
        else:
            is_new_db = True

        if args.skip_archive:
            print("Warning: pages for galleries in archives will not be generated")

        if args.rar:
            print("RARtool path: ", args.rar)

        if args.process:
            print("Process count: ", args.process)

        print("Connecting to HappyPanda database..")
        conn_src = sqlite3.connect(src)
        conn_src.row_factory = sqlite3.Row
        DBBase._DB_CONN = conn_src
        ListDB.init_lists()
        print("Fetching gallery lists..")
        src_galleries = list(GalleryDB.get_all_gallery())
        print("Fetching all galleries, chapters, tags and hashes..")
        print("Fetched galleries count:", len(src_galleries))
        if args.offset > 0:
            src_galleries = src_galleries[args.offset:]
            print(f"Offsetting the amount of galleries to add by {args.offset}")
        if args.limit > 0:
            src_galleries = src_galleries[:args.limit]
            print(f"Limiting the amount of galleries to add by {args.limit}")
        print(f"Total gallery count to add {len(src_galleries)}")
        print("Creating new HappyPanda X database")
        if not is_rfc:
            engine = db.create_engine(os.path.join("sqlite:///", dst))
        else:
            if not database_exists(dst):
                encoding = 'utf8mb4' if 'mysql+pymysql' in dst.lower() else 'utf8'
                create_database(dst, encoding)
            engine = db.create_engine(dst)
        db.Base.metadata.create_all(engine)
        sess = db.scoped_session(db.sessionmaker())
        sess.configure(bind=engine)
        constants.db_session = sess
        db.initEvents(sess)
        s = sess()
        db.init_defaults(s)
        s.autoflush = False
        print("Converting to HappyPanda X Gallery.. ")

        gallery_mixmap = {}
        dst_galleries = []
        dst_profiles = []
        en_lang = db.Language.as_unique(name="English")
        dst_languages = {"english": en_lang}
        dst_aliasnames = {}
        dst_artists = {}
        dst_circles = {}
        dst_parodies = {}
        dst_categories = {}
        dst_namespace = {}
        dst_tag = {}
        dst_nstagmapping = {}
        dst_collections = {}
        dst_grouping = {}
        dst_pages = {}
        dst_pagelist = {}

        pages_to_send = []
        pages_to_send2 = []
        try:
            pages_count = 0
            unique_paths = []
            for numb, g in enumerate(src_galleries):

                if args.debug:
                    print("------------ Gallery ID {} ----------".format(g.id))

                galleries = []
                gallery_ns = None

                for ch in g.chapters:

                    path = g.path if ch.in_archive else ch.path
                    if not os.path.exists(path):
                        try:
                            print("\nSkipping '{}' because path doesn't exists.".format(ch.title))
                        except UnicodeError:
                            print(
                                "\nSkipping '{}' because path doesn't exists.".format(
                                    ch.title.encode(
                                        errors='ignore')))
                        continue

                    if not args.skip_archive:
                        if path.endswith(('.rar', '.cbr')) and not args.rar:
                            try:
                                print("\nSkipping '{}' because path to unrar tool has not been supplied.".format(ch.title))
                            except UnicodeError:
                                print(
                                    "\nSkipping '{}' because path to unrar tool has not been supplied.".format(
                                        ch.title.encode(
                                            errors='ignore')))
                            continue

                    if args.debug:
                        print("Creating gallery from chapter: {}".format(g.path))

                    gallery = db.Gallery()

                    if ch.in_archive:
                        real_path = pathlib.Path(path).joinpath(
                            ch.path[1:] if ch.path.startswith(('/', '\\')) else ch.path)
                    else:
                        real_path = pathlib.Path(ch.path)

                    if not args.delete_target or is_new_db:
                        if db.Gallery.exists_by_path(real_path, obj=False):
                            try:
                                print(
                                    "\nSkipping '{}' because gallery path already exists in target database.".format(
                                        ch.title))
                            except UnicodeError:
                                print(
                                    "\nSkipping '{}' because gallery path already exists in target database".format(
                                        ch.title.encode(
                                            errors='ignore')))
                            continue

                    if ch.in_archive:
                        h = hash((g.path, ch.path))
                        if h in unique_paths:
                            continue
                        unique_paths.append(h)

                        if not args.skip_archive:
                            dst_pages[pages_count] = gallery
                            pages_to_send.append((pages_count, ch.in_archive, ch.path, path, g.path))
                            pages_count += 1

                    else:
                        h = hash((ch.path,))
                        if h in unique_paths:
                            continue
                        unique_paths.append(h)

                        dst_pages[pages_count] = gallery
                        pages_to_send2.append((pages_count, ch.in_archive, ch.path, path, g.path))
                        pages_count += 1

                    # for col in copy.copy(gallery.collections):
                    #    if col.name in dst_collections:
                    #        gallery.collections.remove(col)
                    #        gallery.collections.append(dst_collections[col.name])
                    #    else:
                    #        dst_collections[col.name] = col

                    if gallery_ns is not None:
                        gallery.grouping = gallery_ns
                    else:
                        gallery_ns = db.Grouping.as_unique(name=ch.title if ch.title else g.title)
                        gallery_ns = dst_grouping.get(gallery_ns.name, gallery_ns)
                        dst_grouping[gallery_ns.name] = gallery_ns
                        gallery_ns.galleries.append(gallery)

                        if g.status and g.status.lower() != "unknown":
                            if g.status.lower() == "completed":
                                gstatus = db.Status.as_unique(session=sess, name=db.Status.names.completed)
                            elif g.status.lower() == "ongoing":
                                gstatus = db.Status.as_unique(session=sess, name=db.Status.names.ongoing)
                            else:
                                gstatus = db.Status.as_unique(session=sess, name=g.status)
                        else:
                            gstatus = db.Status.as_unique(session=sess, name=db.Status.names.unknown)

                        gallery_ns.status = gstatus

                    gallery.number = ch.number

                    lang = g.language.lower() if g.language else None
                    if lang and not lang in dst_languages:
                        db_lang = db.Language.as_unique(name=g.language)
                        dst_languages[lang] = db_lang
                    else:
                        db_lang = dst_languages['english']

                    gallery.language = db_lang

                    title = db.Title()
                    title.name = ch.title if ch.title else g.title

                    col_name, n_title, col_category = extract_collection(title.name)
                    if col_name:
                        title.name = n_title
                        collection = dst_collections.get(col_name.lower())
                        if not collection:
                            collection = db.Collection.as_unique(name=col_name)
                            dst_collections[col_name.lower()] = collection
                        collection.galleries.append(gallery)

                        if col_category:
                            col_type = dst_categories.get(col_category.lower())
                            if not col_type:
                                col_type = db.Category.as_unique(name=col_category)
                                dst_categories[col_category.lower()] = col_type
                            collection.category = col_type

                    title.language = db_lang
                    gallery.titles.clear()
                    gallery.titles.append(title)

                    if g.artist:
                        artist_names = []
                        if 'Artist' in g.tags:
                            circle_in_title = False
                            if 'Group' in g.tags:
                                circle_tags = g.tags['Group']
                                for ctag in circle_tags:
                                    if ctag + ' ' in g.artist.lower():
                                        circle_in_title = True
                                        break
                            if circle_in_title:
                                artist_tags = g.tags['Artist']
                                for atag in artist_tags:
                                    artist_various = '(various)' in g.artist.lower()
                                    if '(' + atag + ')' in g.artist.lower() or artist_various:
                                        natag = utils.extract_original_text(atag, g.artist)
                                        if artist_various and natag == atag:
                                            natag = utils.capitalize_text(natag)
                                        artist_names.append(natag)
                        if not artist_names:
                            artist_names.append(g.artist.strip())

                        for a_name in artist_names:
                            artist = dst_artists.get(a_name.lower())
                            if not artist:
                                artist = db.Artist.as_unique(name=a_name)
                            for a in artist.names:
                                if a.name.lower() == a_name.lower():
                                    artist_name = a
                                    break
                            else:
                                artist_name = db.ArtistName.as_unique(name=a_name)
                                artist.names.append(artist_name)

                            if not artist_name.language:
                                artist_name.language = db_lang

                            gallery.artists.append(artist)
                            dst_artists[a_name.lower()] = artist

                            if 'Group' in g.tags:
                                circle_tags = g.tags['Group']
                                for ctag in circle_tags:
                                    if g.artist and ctag in g.artist.lower():
                                        cname = utils.extract_original_text(ctag, g.artist)
                                    else:
                                        cname = utils.capitalize_text(ctag)
                                    if cname:
                                        circle = dst_circles.get(cname.lower())
                                        if not circle:
                                            circle = db.Circle.as_unique(name=cname)
                                            dst_circles[cname.lower()] = circle
                                        if not circle in artist.circles:
                                            artist.circles.append(circle)

                    if not g.info == "No description..":
                        gallery.info = g.info
                    if g.fav:
                        gallery.metatags.append(db.MetaTag.tags[db.MetaTag.names.favorite])
                    if g.view == 2:
                        gallery.metatags.append(db.MetaTag.tags[db.MetaTag.names.inbox])
                    if g.rating is not None:
                        gallery.rating = g.rating * 2
                    if g.type:
                        gtype = dst_categories.get(g.type.lower())
                        if not gtype:
                            gtype = db.Category.as_unique(name=g.type)
                            dst_categories[gtype.name.lower()] = gtype
                        gallery.category = gtype

                    if g.link:
                        gurl = db.Url()
                        gurl.name = g.link
                        gallery.urls.append(gurl)

                    if 'Parody' in g.tags:
                        parody_tags = g.tags['Parody']
                        for ptag in parody_tags:
                            if g.title and ptag in g.title.lower():
                                pname = utils.extract_original_text(ptag, g.title)
                            else:
                                pname = utils.capitalize_text(ptag)
                            if args.debug:
                                print("Parody tag:", ptag)
                            if pname:
                                parody = dst_parodies.get(pname.lower())
                                if not parody:
                                    if args.debug:
                                        print("Adding new parody:", pname)
                                    parody = db.Parody.as_unique(name=pname)
                                    for a in parody.names:
                                        if a.name.lower() == pname.lower():
                                            parody_name = a
                                            break
                                    else:
                                        parody_name = db.ParodyName.as_unique(name=pname)
                                        parody.names.append(parody_name)
                                    if not parody_name.language:
                                        parody_name.language = dst_languages['english']

                                    dst_parodies[pname.lower()] = parody
                                else:
                                    if args.debug:
                                        print("Adding old parody:", pname)
                                gallery.parodies.append(parody)

                    gallery.pub_date = g.pub_date
                    gallery.timestamp = g.date_added
                    gallery.last_read = g.last_read

                    gallery.times_read = g.times_read

                    if gallery.last_read and gallery.times_read:
                        gallery.metatags.append(db.MetaTag.as_unique(session=sess, name=db.MetaTag.names.read))

                    galleries.append(gallery)
                    if not g.id in gallery_mixmap:
                        gallery_mixmap[g.id] = []
                    gallery_mixmap[g.id].append(gallery)

                # tags

                for ns in g.tags:
                    n = constants.special_namespace if ns == 'default' else ns
                    for tag in g.tags[ns]:
                        nstagname = n + tag
                        nstag = db.NamespaceTags.as_unique(n, tag)
                        nstag = dst_nstagmapping.get(nstagname, nstag)
                        dst_nstagmapping[nstagname] = nstag
                        for ch_g in galleries:
                            ch_g.tags.append(nstag)

                dst_galleries.extend(galleries)

                try:
                    print_progress(numb, len(src_galleries), "Progress:", bar_length=50)
                except UnicodeEncodeError:
                    print("\nStill in progress... please wait...")

            if not pages_to_send:
                AMOUNT_OF_TASKS = 1

            page_pool = []
            thread_pool = []

            def create_process(items):
                pipe1, pipe2 = Pipe(False)
                p = Process(target=page_generate, args=(args.rar, items, pipe2), daemon=True)
                p.start()
                page_pool.append(p)
                t = threading.Thread(target=process_pipes, args=(pages_out, pipe1), daemon=True)
                t.start()
                thread_pool.append(t)

            pages_to_send2 = list(split(pages_to_send2, AMOUNT_OF_TASKS))
            pages_to_send = list(split(pages_to_send, AMOUNT_OF_TASKS))

            if len(pages_to_send2) < len(pages_to_send):
                for n, x in enumerate(pages_to_send):
                    try:
                        x.extend(pages_to_send2[n])
                    except IndexError:
                        pass
                pages_to_sendx = pages_to_send
            else:
                for n, x in enumerate(pages_to_send2):
                    try:
                        x.extend(pages_to_send[n])
                    except IndexError:
                        pass
                pages_to_sendx = pages_to_send2

            pages_map = {}
            pages_finish = {}
            pages_finished = []
            for n, x in enumerate(pages_to_sendx):
                pages_map[n] = x
                pages_finish[n] = False
                create_process((n, x))

            print("\nResolving gallery pages...")
            unique_pages = []
            current_p_count = 0
            while current_p_count < pages_count:
                items = pages_out.get()

                # need to make sure process helps with remaining if it finishes its own
                for dead_p in page_pool:
                    if not dead_p.is_alive():
                        dead_p.terminate()
                        if pages_finished:
                            pages_id = pages_finished.pop()
                            for p_id in pages_finish:
                                if not pages_finish[p_id]:
                                    create_process((p_id, list(reversed(pages_map[p_id]))))

                if isinstance(items, int):
                    pages_finished.append(items)
                    pages_finish[items] = True
                    continue

                for item in items:
                    p_hash, g, pages = item
                    p_hash = hash(p_hash)
                    if p_hash in unique_pages:
                        continue
                    unique_pages.append(p_hash)
                    current_p_count += 1
                    for pp in pages:
                        p = db.Page()
                        p.name = pp[0]
                        p.path = pp[1]
                        p.number = pp[2]
                        p.in_archive = pp[3]
                        dst_pagelist.setdefault(dst_pages[g], []).append(p)
                    try:
                        print_progress(current_p_count, pages_count, "Progress:", bar_length=50)
                    except UnicodeEncodeError:
                        print("\nStill in progress... please wait...")
            for p in page_pool:
                p.terminate()
        finally:
            pass

        print("\nCreating gallery lists")
        dst_lists = []
        for l in GALLERY_LISTS:
            glist = db.GalleryFilter.as_unique(name=l.name)
            if not glist.id:
                glist.filter = l.filter
                glist.enforce = l.enforce
                glist.regex = l.regex
                glist.l_case = l.case
                glist.strict = l.strict
            for g in l.galleries():
                if g.id in gallery_mixmap:
                    glist.galleries.extend(gallery_mixmap[g.id])

            dst_lists.append(glist)

        # s.flush()
        #print("Flushing... (this might take a few minutes)")
        #s.bulk_save_objects(dst_taggables, return_defaults=True)
        # s.flush()

        #print("Adding languages...")
        # items.extend(dst_languages.values())
        #print("Adding artists...")
        # items.extend(dst_artists.values())
        #print("Adding gallery types...")
        # items.extend(dst_gtype.values())
        #print("Adding gallery namespaces...")
        # items.extend(dst_namespace.values())
        #print("Adding gallery tags...")
        # items.extend(dst_tag.values())
        # items.extend(dst_nstagmapping.values())
        #print("Adding galleries...")
        # items.extend(dst_galleries)
        #print("Adding gallery lists...")
        # items.extend(dst_lists)
        #s.bulk_save_objects(items, return_defaults=True)

        if args.debug:
            print(f"Created parodies:")
            for p in dst_parodies.values():
                print(p.names)

        print(f"Adding {len(dst_languages)} languages...")
        s.add_all(dst_languages.values())
        print(f"Adding {len(dst_artists)} artists...")
        s.add_all(dst_artists.values())
        print(f"Adding {len(dst_categories)} gallery types...")
        s.add_all(dst_categories.values())
        print(f"Adding {len(dst_nstagmapping)} gallery tags...")
        s.add_all(dst_namespace.values())
        s.add_all(dst_tag.values())
        s.add_all(dst_nstagmapping.values())
        print(f"Adding {len(dst_galleries)} galleries...")
        s.add_all(dst_galleries)
        print(f"Adding {len(dst_lists)} gallery lists...")
        s.add_all(dst_lists)
        print("Flushing... (this might take a few minutes)")
        s.flush()
        taggable_items = []
        page_items = []
        for g, g_pages in dst_pagelist.items():
            for p in g_pages:
                p.gallery_id = g.id
                page_items.append(p)
                taggable_items.append(db.Taggable())
        print(f"Adding {len(page_items)} gallery pages... (this might take a while too)")
        if taggable_items:
            one_taggable = taggable_items[0]
            s.add(one_taggable)
            s.flush()
            s.bulk_save_objects(taggable_items[1:], return_defaults=True)
            print("Flushing again... (last one, i-I swear, don't be mad..)")
            s.flush()
            del taggable_items
            taggable_items = list(s.query(db.Taggable.id).filter(db.Taggable.id > one_taggable.id).all())
            taggable_items.insert(0, (one_taggable.id,))
        for n, p in enumerate(page_items):
            p.taggable_id = taggable_items[n][0]
        s.bulk_save_objects(page_items, return_defaults=True)
        print("Committing...")
        s.commit()
        print("Done!")
    except Exception as e:
        print(e)
        raise


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
