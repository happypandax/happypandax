"""
Database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from happypanda.common import constants, utils, exceptions
from happypanda.core import db, services, message
from happypanda.interface import enums
from happypanda.core.commands import database_cmd

import functools


def _get_image(kwargs, cover):
    return message.Profile(cover, **kwargs) if cover else None


def get_image(item_type: enums.ItemType=enums.ItemType.Gallery,
              item_ids: list=[],
              size: enums.ImageSize=enums.ImageSize.Medium,
              url: bool=False,
              uri: bool=False):
    """
    Get image for item.
    Image content is base64 encoded.

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Artist`,
            :py:attr:`.ItemType.Collection`, :py:attr:`.ItemType.Grouping`, :py:attr:`.ItemType.Page`
        item_ids: list of item ids
        size: size of image
        url: replace image content with url to image file
        uri: turn raw base64 string into an URI

    Returns:
        .. code-block:: guess

            {
                item_id : async_command_id
            }
    """

    item_type = enums.ItemType.get(item_type)
    size = enums.ImageSize.get(size)

    _, db_item = item_type._msg_and_model(
        (enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Grouping, enums.ItemType.Page,
         enums.ItemType.Artist))

    content = {}

    command_dec = functools.partial(_get_image, {'url': url, 'uri': uri})

    for i in item_ids:
        c = database_cmd.GetModelImage()
        services.ImageService.generic.add_command(c, command_dec)
        content[i] = c.start(db_item, i, size)

    return message.Identity('image', content)


def get_item(item_type: enums.ItemType=enums.ItemType.Gallery,
             item_id: int=0):
    """
    Get item

    Args:
        item_type: type of item to get
        item_id: id of item

    Returns:
        item message object
    """

    item_type = enums.ItemType.get(item_type)

    db_msg, db_model = item_type._msg_and_model()

    item = database_cmd.GetModelItemByID().run(db_model, {item_id})[0]
    if not item:
        raise exceptions.DatabaseItemNotFoundError(utils.this_function(),
                                                   "'{}' with id '{}' was not found".format(item_type.name,
                                                                                            item_id))

    return db_msg(item)


def get_items(item_type: enums.ItemType=enums.ItemType.Gallery,
              limit: int=100):
    """
    Get a list of items

    Args:
        item_type: type of item to get
        limit: limit the amount of items returned

    Returns:
        .. code-block:: guess

            [
                item message object,
                ...
            ]
    """

    item_type = enums.ItemType.get(item_type)

    db_msg, db_model = item_type._msg_and_model()

    items = database_cmd.GetModelItems().run(db_model, limit=limit)

    item_list = message.List(db.model_name(db_model), db_msg)
    [item_list.append(db_msg(i)) for i in items]
    return item_list


def get_related_items(item_type: enums.ItemType=enums.ItemType.Gallery,
                      item_id: int = 0,
                      related_type: enums.ItemType=enums.ItemType.Page,
                      limit: int = 100):
    """
    Get item related to given item

    Args:
        item_type: parent item
        item_id: id of parent item
        related_type: child item
        limit: limit the amount of items returned

    Returns:
        .. code-block:: guess

            [
                related item message object,
                ...
            ]
    """
    item_type = enums.ItemType.get(item_type)
    related_type = enums.ItemType.get(related_type)

    _, parent_model = item_type._msg_and_model()
    child_msg, child_model = related_type._msg_and_model()

    col = db.relationship_column(parent_model, child_model)
    if not col:
        raise exceptions.APIError(
            utils.this_function(),
            "{} has no relationship with {}".format(
                related_type,
                item_type))

    s = constants.db_session()
    item_ids = s.query(child_model.id).join(col).filter(parent_model.id == item_id).limit(limit).all()
    items = database_cmd.GetModelItemByID().run(child_model, {x[0] for x in item_ids})

    item_list = message.List(db.model_name(child_model), child_msg)
    [item_list.append(child_msg(x)) for x in items]
    return item_list


def get_count(item_type: enums.ItemType=enums.ItemType.Gallery):
    """
    Get count of items in the database

    Args:
        item_type: type of item

    Returns:
        .. code-block:: guess

            {
                'count' : int
            }
    """

    item_type = enums.ItemType.get(item_type)

    _, db_model = item_type._msg_and_model()

    s = constants.db_session()

    return message.Identity('count', {'count': s.query(db_model).count()})


def get_related_count(item_type: enums.ItemType=enums.ItemType.Gallery,
                      item_id: int = 0,
                      related_type: enums.ItemType=enums.ItemType.Page):
    """
    Get count of items related to given item

    Args:
        item_type: parent item
        item_id: id of parent item
        related_type: child item

    Returns:
        .. code-block:: guess

            {
                'id' : int
                'count' : int
            }
    """
    item_type = enums.ItemType.get(item_type)
    related_type = enums.ItemType.get(related_type)

    _, parent_model = item_type._msg_and_model()
    child_msg, child_model = related_type._msg_and_model()

    col = db.relationship_column(parent_model, child_model)
    if not col:
        raise exceptions.APIError(
            utils.this_function(),
            "{} has no relationship with {}".format(
                related_type,
                item_type))

    s = constants.db_session()
    count = s.query(child_model.id).join(col).filter(parent_model.id == item_id).count()
    return message.Identity('count', {'id': item_id, 'count': count})
