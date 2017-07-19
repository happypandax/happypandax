from happypanda.common import constants
from happypanda.core import db, message
from happypanda.interface import enums


def add_gallery(galleries: list=[], paths: list=[], ctx=None):
    """
    Add galleries to the database.

    Args:
        galleries: list of gallery objects parsed from XML
        paths: list of paths to the galleries

    Returns:
        Gallery objects
    """
    return message.Message("works")


def scan_gallery(paths: list=[], add_after: bool=False,
                 ignore_exist: bool=True, ctx=None):
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

def gallery_count(id: int=0, item_type: enums.ItemType=enums.ItemType.GalleryFilter):
    """
    Get gallery count

    Args:
        id: id of item
        item_type: can be 'GalleryList', 'Collection' or 'Grouping'

    Returns:
        ```
        { 'id': id, 'count':int }
        ```
    """

    item_type = enums.ItemType.get(item_type)

    _, db_item = item_type._msg_and_model((enums.ItemType.GalleryList, enums.ItemType.Collection, enums.ItemType.Grouping))

    s = constants.db_session()

    return message.Identity("gcount", {
            'id': id, 'count': s.query(db_item).join(db_item.galleries).filter(db_item.id == id).count()})
