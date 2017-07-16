from happypanda.common import constants, utils, exceptions
from happypanda.core import db, services, message
from happypanda.interface import enums
from happypanda.core.commands import database_cmd

import functools


def _get_cover(kwargs, cover):
    return message.Profile(cover, **kwargs) if cover else None


def get_cover(item_type: enums.ItemType = enums.ItemType.Gallery.name,
              item_ids: list = [],
              size: enums.ImageSize = enums.ImageSize.Medium.name,
              local: bool = False,
              uri: bool = False,
              ctx=None):
    """
    Get cover image

    Args:
        item_type: ...
        item_ids: list of item ids
        size: ...
        local: replace image content with local path to image file

    Returns:
        a dict of item_id:async_command_id

    """
    utils.require_context(ctx)

    item_type = enums.ItemType.get(item_type)
    size = enums.ImageSize.get(size)

    db_items = {
        enums.ItemType.Gallery: db.Gallery,
        enums.ItemType.Collection: db.Collection,
        enums.ItemType.Grouping: db.Grouping,
        enums.ItemType.Page: db.Page,
    }

    db_item = db_items.get(item_type)

    content = {}

    command_dec = functools.partial(_get_cover, {'local': local, 'uri': uri})

    for i in item_ids:
        c = database_cmd.GetModelCover()
        services.ImageService.generic.add_command(c, command_dec)
        content[i] = c.start(db_item, i, size)

    return message.Identity('cover', content)


def get_item(item_type: enums.ItemType = enums.ItemType.Gallery.name,
             item_id: int = 0):
    """
    Get item

    Args:
        item_type: ...
        item_id: id of item

    Returns:
        item message object
    """

    item_type = enums.ItemType.get(item_type)

    db_items = {
        enums.ItemType.Gallery: (db.Gallery, message.Gallery),
        enums.ItemType.Collection: (db.Collection, message.Collection),
        enums.ItemType.Grouping: (db.Grouping, message.Grouping),
        enums.ItemType.Page: (db.Page, message.Page),
    }

    db_model = db_items.get(item_type)
    if not db_model:
        raise exceptions.APIError(
            "Item type must be on of {}".format(
                db_items.keys()))

    db_model, db_msg = db_model

    item = database_cmd.GetModelItemByID().run(db_model, {item_id})[0]
    if not item:
        raise exceptions.DatabaseItemNotFoundError(utils.this_function(), "'{}' with id '{}' was not found".format(item_type.name, item_id))

    return db_msg(item)

def _get_glists():
    s = constants.db_session()
    return s.query(db.GalleryFilter).all()


def get_glists():
    """
    Get a list of gallery lists

    Returns:
        a list of gallerylist objects
    """

    glists = message.List("gallerylist", message.GalleryFilter)
    [glists.append(message.GalleryFilter(x)) for x in _get_glists()]
    return glists


def get_tags(taggable_id: int = 0):
    ""
    pass


def _get_count(item_type: enums.ItemType = enums.ItemType.Gallery.name):
    ""

    item_type = enums.ItemType.get(item_type)

    db_items = {
        enums.ItemType.Gallery: db.Gallery,
        enums.ItemType.Collection: db.Collection,
        enums.ItemType.Grouping: db.Grouping,
    }

    db_item = db_items.get(item_type)

    s = constants.db_session()
    return s.query(db_item).count()


def get_count(item_type: enums.ItemType = enums.ItemType.Gallery.name):
    """
    Get count of items in the database

    Args:
     item_type: type of db item (Gallery, Collection, Grouping)

    Returns:
        {'count': int}
    """

    return message.Identity('count', {'count': _get_count(item_type)})
