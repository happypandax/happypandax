from happypanda.common import constants, message
from happypanda.core import db
from happypanda.interface import enums


def add_gallery(galleries: list = [], paths: list = [], ctx=None):
    """
    Add galleries to the database.

    Args:
        galleries: list of gallery objects parsed from XML
        paths: list of paths to the galleries

    Returns:
        Gallery objects
    """
    return message.Message("works")


def scan_gallery(paths: list = [], add_after: bool = False,
                 ignore_exist: bool = True, ctx=None):
    """
    Scan folders for galleries

    Args:
        paths: list of paths to folders to scan for galleries
        add_after: add found galleries after scan
        ignore_exist: ignore existing galleries

    Returns:
        list of paths to the galleries
    """
    return message.Message("works")


def _gallery_count(
        id: int = 0, item_type: enums.ItemType = enums.ItemType.GalleryFilter.name):

    item_type = enums.ItemType.get(item_type)

    db_items = {
        enums.ItemType.GalleryList: db.GalleryFilter,
        enums.ItemType.Collection: db.Collection,
        enums.ItemType.Grouping: db.Grouping
    }

    db_item = db_items.get(item_type)

    s = constants.db_session()
    return s.query(db_item).join(
        db_item.galleries).filter(
        db_item.id == id).count()


def gallery_count(
        id: int = 0, item_type: enums.ItemType = enums.ItemType.GalleryFilter.name):
    """
    Get gallery count

    Params:
        id: id of item
        item_type: can be 'GalleryList', 'Collection' or 'Grouping'

    Returns:
        {
        'id': id
        'count':int
        }
    """

    return message.Identity(
        "gcount", {
            'id': id, 'count': _gallery_count(
                id, item_type)})
