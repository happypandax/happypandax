from happypanda.common import constants, message, exceptions
from happypanda.server.core import db
from happypanda.server.interface import enums

def library_view(ctx=None,
                 item_type=enums.ItemType.Gallery.name,
                 page=0,
                 limit=100,
                 search_filter="",
                 list_id=None,
                 gallery_filter=enums.GalleryFilter.Library.name):
    """
    Fetch items from the database.
    Provides pagination.

    Params:
        - item_type -- type of items to show ...
        - page -- current page
        - limit -- amount of items per page
        - search_filter -- filter item by search terms
        - list_id -- current item list id
        - gallery_filter -- ...

    Returns:
        list of item message objects
    """
    gallery_filter = enums.GalleryFilter.get(gallery_filter)
    item_type = enums.ItemType.get(item_type)

    db_items = {
        enums.ItemType.Gallery : (db.Gallery, message.Gallery),
        enums.ItemType.Collection : (db.Collection, message.Collection),
        }

    db_item = db_items.get(item_type)
    if not db_item:
        raise exceptions.APIError("Item type must be on of {}".format(db_items.keys()))
    db_item, db_msg = db_item

    s = constants.db_session()
    items = message.List(db_item.__name__.lower(), db_msg)

    q = s.query(db_item).limit(limit)
    [items.append(db_msg(x)) for x in q.all()]

    return items

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


