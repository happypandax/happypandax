from happypanda.common import constants, message, exceptions, utils
from happypanda.server.core import db
from happypanda.server.interface import enums

def library_view(item_type=enums.ItemType.Gallery.name,
                 page=0,
                 search_filter="",
                 list_id=None,
                 gallery_filter=enums.GalleryFilter.Library.name,
                 ctx=None):
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
    utils.require_context(ctx)

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

    q = s.query(db_item).limit(20)
    [items.append(db_msg(x)) for x in q.all()]

    return items