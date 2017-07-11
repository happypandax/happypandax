from happypanda.common import exceptions, utils
from happypanda.core import db, message
from happypanda.interface import enums
from happypanda.core.commands import database_cmd, search_cmd


def library_view(item_type: enums.ItemType = enums.ItemType.Gallery.name,
                 page: int = 0,
                 limit: int = 100,
                 sort_by: str = "",
                 search_query: str = "",
                 filter_id: int = None,
                 view_filter: enums.ViewType = enums.ViewType.Library.name,
                 ctx=None):
    """
    Fetch items from the database.
    Provides pagination.

    Args:
        item_type: type of items to show ...
        page: current page (zero-indexed)
        order_by: name of column to order by ...
        limit: amount of items per page
        search_query: filter item by search terms
        filter_id: current filter list id
        view_filter: ...

    Returns:
        list of item message objects
    """
    utils.require_context(ctx)

    view_filter = enums.ViewType.get(view_filter)
    item_type = enums.ItemType.get(item_type)

    db_items = {
        enums.ItemType.Gallery: (db.Gallery, message.Gallery),
        enums.ItemType.Collection: (db.Collection, message.Collection),
        enums.ItemType.Grouping: (db.Grouping, message.Grouping),
    }

    db_model = db_items.get(item_type)
    if not db_model:
        raise exceptions.APIError(
            "Item type must be on of {}".format(
                db_items.keys()))
    db_model, db_msg = db_model

    items = message.List(db_model.__name__.lower(), db_msg)

    model_ids = search_cmd.ModelFilter().run(db_model, search_query)

    [items.append(db_msg(x)) for x in database_cmd.GetModelItemByID().run(
        db_model, model_ids, limit=limit, offset=page * limit)]

    return items
