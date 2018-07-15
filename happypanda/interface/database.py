"""
Database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import functools

from happypanda.common import constants, utils, exceptions, hlogger
from happypanda.core import db, services, message
from happypanda.interface import enums, helpers
from happypanda.core.commands import database_cmd, search_cmd

log = hlogger.Logger(constants.log_ns_command + __name__)


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
        url: replace image content with http url to image file
        uri: turn raw base64 string into an URI

    Returns:
        .. code-block:: guess

            {
                item_id : command_id
            }

    .. seealso::

        :func:`.get_image_from_path`
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

# def delete_item(item_type: enums.ItemType=enums.ItemType.Gallery,
#             item_id: int=0,
#             options: dict={}):
#    """
#    Create a new item and add it to the database

#    Args:
#        item_type: type of item to create
#        item_id: id of item

#    Returns:
#        []

#    |async command|

#    """

#    item_type = enums.ItemType.get(item_type)
#    db_msg, db_model = item_type._msg_and_model()

#    item = database_cmd.GetModelItems().run(db_model, {item_id})[0]
#    if not item:
#        raise exceptions.DatabaseItemNotFoundError(utils.this_function(),
#                                                   "'{}' with id '{}' was not found".format(item_type.name,
#                                                                                            item_id))


#    cmd_id = database_cmd.DeleteItem(services.AsyncService.generic).run(item, options=options)
#    return message.Identity('command_id', cmd_id)

def new_item(item_type: enums.ItemType=enums.ItemType.Gallery,
             item: dict={},
             options: dict={}):
    """
    Create a new item and add it to the database

    Args:
        item_type: type of item to create
        item: item messeage object

    Returns:
        []

    |async command|

    """

    if not item:
        raise exceptions.APIError(utils.this_function(), "item must be a message object")
    if item.get('id', False) and not constants.dev:
        raise exceptions.APIError(utils.this_function(), "cannot create item with an id")

    item_type = enums.ItemType.get(item_type)
    db_msg, db_model = item_type._msg_and_model()

    db_obj = db_msg.from_json(item)

    cmd_id = database_cmd.AddItem(services.AsyncService.generic).run(db_obj, options=options)
    return message.Identity('command_id', cmd_id)


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
    if not item_id:
        raise exceptions.APIError(utils.this_function(), f"A valid item id is required, not {item_id}")
    item_type = enums.ItemType.get(item_type)

    db_msg, db_model = item_type._msg_and_model()

    item = database_cmd.GetModelItems().run(db_model, {item_id})[0]
    if not item:
        raise exceptions.DatabaseItemNotFoundError(utils.this_function(),
                                                   "'{}' with id '{}' was not found".format(item_type.name,
                                                                                            item_id))

    return db_msg(item)

# def new_items(item_type: enums.ItemType=enums.ItemType.Gallery,
#             items: list={}):
#    """
#    Create new items and add them to the database

#    Args:
#        item_type: type of item to create
#        item: item messeage object

#    Returns:
#        [
#            {
#                item_id : 0, # id of created item, will be 0 if item was not created
#            },
#            ...
#        ]
#    """

#    item_type = enums.ItemType.get(item_type)
#    raise NotImplementedError


def get_items(item_type: enums.ItemType=enums.ItemType.Gallery,
              limit: int=100,
              offset: int=None,
              ):
    """
    Get a list of items

    Args:
        item_type: type of item to get
        limit: limit the amount of items returned
        offset: offset the results by n items

    Returns:
        .. code-block:: guess

            [
                item message object,
                ...
            ]
    """

    item_type = enums.ItemType.get(item_type)

    db_msg, db_model = item_type._msg_and_model()

    items = database_cmd.GetModelItems().run(db_model, limit=limit, offset=offset)

    item_list = message.List(db.model_name(db_model), db_msg)
    [item_list.append(db_msg(i)) for i in items]
    return item_list


def get_related_items(item_type: enums.ItemType=enums.ItemType.Gallery,
                      item_id: int = 0,
                      related_type: enums.ItemType=enums.ItemType.Page,
                      limit: int = 100,
                      offset: int=None,
                      ):
    """
    Get item related to given item

    Args:
        item_type: parent item
        item_id: id of parent item
        related_type: child item
        limit: limit the amount of items returned
        offset: offset the results by n items

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
    q = s.query(child_model.id).join(col).filter(parent_model.id == item_id)
    if offset:
        q = q.offset(offset)
    item_ids = q.limit(limit).all()
    items = database_cmd.GetModelItems().run(child_model, {x[0] for x in item_ids})

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


def search_item(item_type: enums.ItemType=enums.ItemType.Gallery,
                search_query: str = "",
                search_options: dict = {},
                sort_by: enums.ItemSort = None,
                sort_desc: bool=False,
                full_search: bool=True,
                limit: int=100,
                offset: int=None,
                ):
    """
    Search for item

    Args:
        item_type: all of :py:attr:`.ItemType` except :py:attr:`.ItemType.Page` and :py:attr:`.ItemType.GalleryFilter`
        search_query: filter item by search terms
        search_options: options to apply when filtering, see :ref:`Settings` for available search options
        sort_by: either a :py:class:`.ItemSort` or a sort index
        sort_desc: order descending (default is ascending)
        limit: amount of items
        offset: offset the results by n items

    Returns:
        .. code-block:: guess

            [
                item message object,
                ...
            ]

    .. seealso::

        :func:`.get_sort_indexes`
    """
    item_type = enums.ItemType.get(item_type)

    if search_options:
        search_option_names = [x.name for x in search_cmd._get_search_options()]
        for n in search_options:
            if n not in search_option_names:
                raise exceptions.APIError(utils.this_function(), "Invalid search option name '{}'".format(n))

    if item_type in (enums.ItemType.Page, enums.ItemType.GalleryFilter):
        raise exceptions.APIError(utils.this_function(),
                                  "Unsupported itemtype {}".format(item_type))
    db_msg, db_model = item_type._msg_and_model()

    model_ids = set()
    if full_search:
        model_ids = search_cmd.ModelFilter().run(db_model, search_query, search_options)

    items = message.List("items", db_msg)

    order_exp, group_exp, join_exp = helpers._sort_helper(sort_by, sort_desc, db_model)

    [items.append(db_msg(x)) for x in database_cmd.GetModelItems().run(db_model, model_ids, limit=limit, offset=offset,
                                                                       join=join_exp, order_by=order_exp, group_by=group_exp)]

    return items


# def get_random_items(item_type: enums.ItemType=enums.ItemType.Gallery,
#                    limit: int = 1,
#                    item_id: int = None,
#                    search_query: str = "",
#                    filter_id: int = None,
#                    view_filter: enums.ViewType = enums.ViewType.Library,
#                    related_type: enums.ItemType = None,
#                    search_options: dict = {}
#                    ):
#    """
#    Get a random item

#    Args:
#        item_type: type of item
#        limit: amount of items
#        search_query: filter item by search terms
#        search_options: options to apply when filtering, see :ref:`Settings` for available search options
#        filter_id: current :py:attr:`.ItemType.GalleryFilter` item id
#        view_filter: type of view, set ``None`` to not apply any filter
#        related_type: child item
#        item_id: id of parent item
#    """

def update_metatags(item_type: enums.ItemType=enums.ItemType.Gallery,
                    item_id: int=0,
                    metatags: dict={}):
    """
    Update metatags for an item

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Page`,
            :py:attr:`.ItemType.Artist`, :py:attr:`.ItemType.Collection`
        item_id: id of item
        metatag: a dict of ``{ metatag_name : bool }``

    Returns:
        bool indicating whether metatags were updated
    """

    item_type = enums.ItemType.get(item_type)

    _, db_item = item_type._msg_and_model(
        (enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Page,
         enums.ItemType.Artist))

    t = database_cmd.GetModelItems().run(db_item, {item_id})
    if not t:
        raise exceptions.DatabaseItemNotFoundError(
            utils.this_function(),
            "{} with item id '{}' not found".format(
                item_type,
                item_id))
    t = t[0]
    mtags = {}
    anames = db.MetaTag.all_names()
    for m, v in metatags.items():
        if m not in anames:
            raise exceptions.APIError(utils.this_function(), f"Metatag name '{m}' does not exist")
        mtags[m] = v

    t.update("metatags", mtags)

    db.object_session(t).commit()

    return message.Identity('status', True)
