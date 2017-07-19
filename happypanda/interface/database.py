from happypanda.common import constants, utils, exceptions
from happypanda.core import db, services, message
from happypanda.interface import enums
from happypanda.core.commands import database_cmd

import functools


def _get_cover(kwargs, cover):
    return message.Profile(cover, **kwargs) if cover else None


def get_cover(item_type: enums.ItemType = enums.ItemType.Gallery,
              item_ids: list = [],
              size: enums.ImageSize = enums.ImageSize.Medium,
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

    _, db_item = item_type._msg_and_model((enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Grouping, enums.ItemType.Page))

    content = {}

    command_dec = functools.partial(_get_cover, {'local': local, 'uri': uri})

    for i in item_ids:
        c = database_cmd.GetModelCover()
        services.ImageService.generic.add_command(c, command_dec)
        content[i] = c.start(db_item, i, size)

    return message.Identity('cover', content)


def get_item(item_type: enums.ItemType = enums.ItemType.Gallery,
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

    db_msg, db_model = item_type._msg_and_model()

    item = database_cmd.GetModelItemByID().run(db_model, {item_id})[0]
    if not item:
        raise exceptions.DatabaseItemNotFoundError(
            utils.this_function(),
            "'{}' with id '{}' was not found".format(
                item_type.name,
                item_id))

    return db_msg(item)

def get_related_items(item_type: enums.ItemType = enums.ItemType.Gallery,
                     related_type: enums.ItemType = enums.ItemType.Page,
                     item_id: int = 0, limit: int = 100):
    """
    Get item related to given item

    Args:
        item_type: ...
        related_type: ...
        related_id: id of the related item
        limit: limit the amount of items returned

    Returns:
        a list of item message object
    """
    item_type = enums.ItemType.get(item_type)
    related_type = enums.ItemType.get(related_type)

    db_msg, db_model = item_type._msg_and_model()

    s = constants.db_session()

    item_ids = s.query(db_model.id).filter


def get_gfilters():
    """
    Get a list of gallery filter lists

    Returns:
        a list of galleryfilter objects
    """

    glists = message.List("gallerylist", message.GalleryFilter)
    s = constants.db_session()
    [glists.append(message.GalleryFilter(x)) for x in s.query(db.GalleryFilter).all()]
    return glists


def get_tags(taggable_id: int = 0):
    ""
    pass


def get_count(item_type: enums.ItemType = enums.ItemType.Gallery):
    """
    Get count of items in the database

    Args:
     item_type: type of db item (Gallery, Collection, Grouping)

    Returns:
        {'count': int}
    """

    item_type = enums.ItemType.get(item_type)

    _, db_model = item_type._msg_and_model()

    s = constants.db_session()

    return message.Identity('count', {'count': s.query(db_model).count()})
