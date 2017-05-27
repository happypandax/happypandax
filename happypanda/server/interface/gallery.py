from happypanda.common import constants, message, exceptions, utils
from happypanda.server.core import db
from happypanda.server.interface import enums


def _add_gallery(ctx=None, galleries=[], paths=[]):
    pass


def add_gallery(ctx=None, galleries=[], paths=[]):
    """
    Add galleries to the database.

    Params:
        - galleries -- list of gallery objects parsed from XML

            Returns:
                Status

        - paths -- list of paths to the galleries

    Returns:
        Gallery objects
    """
    return message.Message("works")


def _scan_gallery(ctx=None, paths=[], add_after=False, ignore_exist=True):
    pass


def scan_gallery(ctx=None, paths=[], add_after=False, ignore_exist=True):
    """
    Scan folders for galleries

    Params:
        - paths -- list of paths to folders to scan for galleries
        - add_after -- add found galleries after scan
        - ignore_exist -- ignore existing galleries

    Returns:
        list of paths to the galleries
    """
    return message.Message("works")


def _gallery_count(id=0, item_type=enums.ItemType.GalleryList.name):

    item_type = enums.ItemType.get(item_type)

    db_items = {
        enums.ItemType.GalleryList: db.GalleryList,
        enums.ItemType.Collection: db.Collection,
        enums.ItemType.Grouping: db.Grouping
    }

    db_item = db_items.get(item_type)

    s = constants.db_session()
    return s.query(db_item).join(
        db_item.galleries).filter(
        db_item.id == id).count()


def gallery_count(id=0, item_type=enums.ItemType.GalleryList.name):
    """
    Get gallery count

    Params:
        - id -- id of item
        - item_type -- can be 'GalleryList', 'Collection' or 'Grouping'

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
