"""
Gallery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import os
import functools

from happypanda.common import exceptions, utils, constants, hlogger
from happypanda.core.commands import database_cmd, io_cmd, gallery_cmd
from happypanda.core import message, db, services
from happypanda.interface import enums

log = hlogger.Logger(__name__)


# def add_gallery(galleries: list=[], paths: list=[]):
#    """
#    Add galleries to the database.

#    Args:
#        galleries: list of gallery objects
#        paths: list of paths to the galleries

#    Returns:
#        Gallery objects
#    """
#    return message.Message("works")


# def scan_gallery(paths: list=[], add_after: bool=False,
#                 ignore_exist: bool=True):
#    """
#    Scan folders for galleries

#    Args:
#        paths: list of paths to folders to scan for galleries
#        add_after: add found galleries after scan
#        ignore_exist: ignore existing galleries

#    Returns:
#        list of paths to the galleries
#    """
#    return message.Message("works")

def _get_similar(kwargs, similar_items):
    item_list = message.List(db.model_name(kwargs['db_model']), kwargs['db_msg'])
    items = []
    if similar_items:
        similar_items = similar_items[:kwargs['limit']]
        db_items = {}  # needed to sort them the way they came in
        for g in database_cmd.GetModelItems().run(kwargs['db_model'], set(similar_items)):
            db_items[g.id] = g
        [items.append(db_items[x]) for x in similar_items if x in db_items]

    [item_list.append(kwargs['db_msg'](x)) for x in items]
    return item_list


def get_similar(item_type: enums.ItemType=enums.ItemType.Gallery,
                item_id: int = 0,
                limit=10):
    """
    Get similar items

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`
        item_id: id of item
        limit: amount of items

    Returns:
        .. code-block:: guess

            [
                item message object,
                ...
            ]

    |async command|
    """
    item_type = enums.ItemType.get(item_type)
    db_msg, db_model = item_type._msg_and_model(
        (enums.ItemType.Gallery,))
    c = gallery_cmd.SimilarGallery()
    services.AsyncService.generic.add_command(c, functools.partial(_get_similar,
                                                                   {'limit': limit,
                                                                    'db_model': db_model,
                                                                    'db_msg': db_msg}))
    return message.Identity('command', c.start(item_id))


def source_exists(item_type: enums.ItemType=enums.ItemType.Gallery,
                  item_id: int = 0,
                  check_all: bool=False):
    """
    Check if gallery/page source exists on disk

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Page`
        item_id: id of item
        check_all: goes through all pages and checks them, default behaviour is to only check parent files/folders. Only relevant for :py:attr:`.ItemType.Gallery`

    Returns:
        .. code-block:: guess

            {
                'exists' : bool
                'missing' : [
                    {'id': int, 'item_type': item_type},
                    ...
                    ]
            }

    """

    item_type = enums.ItemType.get(item_type)

    _, db_model = item_type._msg_and_model((enums.ItemType.Gallery, enums.ItemType.Page))

    if item_type == enums.ItemType.Page:
        item = database_cmd.GetModelItems().run(db_model, {item_id}, columns=(db.Page.path,))
    elif item_type == enums.ItemType.Gallery:
        item = database_cmd.GetModelItems().run(db_model, {item_id}, columns=(db.Gallery.single_source,))

    if not item:
        raise exceptions.DatabaseItemNotFoundError(utils.this_function(),
                                                   "'{}' with id '{}' was not found".format(item_type.name,
                                                                                            item_id))
    else:
        item = item[0]

    paths = {}
    not_empty = True
    if item_type == enums.ItemType.Page:
        paths[item_id] = (item[0], item_type.value)
    elif item_type == enums.ItemType.Gallery:
        s = constants.db_session()
        if item and not check_all:
            p = s.query(db.Page.path).filter(db.Gallery.id == item_id).first()
            if p:
                paths[item_id] = (os.path.split(p[0])[0], item_type.value)
            else:
                not_empty = True
        else:
            ps = s.query(db.Page.id, db.Page.path).filter(db.Page.gallery_id == item_id).all()
            for p in ps:
                paths[p[0]] = (p[1], enums.ItemType.Page.value)
            not_empty = bool(ps)

    missing = []
    for t_id in paths:
        src, t_type = paths[t_id]
        try:
            e = io_cmd.CoreFS(src).exists
        except exceptions.ArchiveExistError:
            e = False
        if not e:
            missing.append({'id': t_id, 'item_type': t_type})

    return message.Identity("exists", {'exists': not missing and not_empty, 'missing': missing})


def get_page(page_id: int=None, gallery_id: int=None, number: int=None, prev: bool=False):
    """
    Get next/prev page by either gallery or page id

    Args:
        page_id: id of page
        gallery_id: id of gallery
        number: retrieve specific page number
        prev: by default next page is retrieved, to retrieve prev page set this to true

    Returns:
        Page object
    """
    if not (gallery_id or page_id):
        raise exceptions.APIError(
            utils.this_function(),
            "Either a gallery id or page id is required")

    if number is None:
        number = 0

    item = None

    if page_id:
        p = database_cmd.GetModelItems().run(db.Page, {page_id})[0]
        if number and p and number == p.number:
            item = p
        elif p:
            number = number or p.number
            gallery_id = p.gallery_id

    if not item:
        f = db.Page.number < number if prev else db.Page.number == number
        f = db.and_op(f, db.Page.gallery_id == gallery_id)
        item = database_cmd.GetModelItems().run(db.Page,
                                                order_by=db.Page.number.desc() if prev else db.Page.number,
                                                filter=f,
                                                limit=1)
        if item:
            item = item[0]

    return message.Page(item) if item else None

# def save_for_later():
#    pass


def open_gallery(item_id: int=0, item_type: enums.ItemType = enums.ItemType.Gallery, viewer_args: str=None):
    """
    Open a gallery or page in an external viewer

    Args:
        item_id: id of item
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Page`
        viewer_args: commandline arguments to supply the viewer, overriding the default viewer arguments specified in settings

    Returns:
        bool indicating if item was successfully opened
    """
    item_type = enums.ItemType.get(item_type)

    _, db_model = item_type._msg_and_model((enums.ItemType.Gallery, enums.ItemType.Page))
    kwargs = {}
    if item_type == enums.ItemType.Page:
        p = database_cmd.GetModelItems().run(db_model, {item_id}, columns=(db_model.gallery_id, db_model.number))
    else:
        p = database_cmd.GetModelItems().run(db_model, {item_id})
    if not p:
        raise exceptions.DatabaseItemNotFoundError(
            utils.this_function(),
            "{} with item id '{}' not found".format(
                item_type,
                item_id))
    p = p[0]
    if item_type == enums.ItemType.Page:
        kwargs['gallery_or_id'] = p[0]
        kwargs['number'] = p[1]
    else:
        kwargs["gallery_or_id"] = p

    if viewer_args:
        kwargs['args'] = tuple(x.strip() for x in viewer_args.split())

    opened = gallery_cmd.OpenGallery().run(**kwargs)

    return message.Identity("status", opened)


def scan_galleries(path: str, scan_options: dict = {}):
    """
    Scan for galleries in the given directory/archive

    Args:
        path: path to directory/archive that exists on this system
        scan_options: options to apply to the scanning process, see :ref:`Settings` for available scanning options

    Returns:
        .. code-block:: guess

            {
                'command_id': int,
                'view_id': int
            }

    |async command|

    |temp view|
    """
    path = io_cmd.CoreFS(path)
    if not path.exists:
        raise exceptions.CoreError(utils.this_function(), f"Path does not exists on this system: '{path.path}'")

    view_id = next(constants.general_counter)
    cmd_id = gallery_cmd.ScanGallery(services.AsyncService.generic).run(path, scan_options, view_id=view_id)

    return message.Identity('data', {'command_id': cmd_id,
                                     'view_id': view_id})


def load_gallery_from_path(path: str = ""):
    """
    Load gallery data from a path

    Args:
        path: a supported path (note that the path must exist on this system if path points to a file/directory)

    Returns:
        .. code-block:: guess

            a GalleryFS message object

    """
    gfs = io_cmd.GalleryFS(path)
    gfs.load_metadata()
    gfs.load_pages()
    gfs.check_exists()
    return message.GalleryFS(gfs)
