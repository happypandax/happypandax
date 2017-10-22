"""
UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import i18n

from happypanda.common import utils, constants, exceptions, hlogger, config
from happypanda.core import message, db
from happypanda.interface import enums
from happypanda.core.commands import database_cmd, search_cmd

log = hlogger.Logger(__name__)

i18n.load_path.append(constants.dir_translations)
i18n.set("file_format", "yaml")
i18n.set("filename_format", "{locale}.{namespace}.{format}")
i18n.set("error_on_missing_translation", True)


def _view_helper(item_type: enums.ItemType=enums.ItemType.Gallery,
                 search_query: str = "",
                 filter_id: int = None,
                 view_filter: enums.ViewType = enums.ViewType.Library,
                 item_id: int = None,
                 related_type: enums.ItemType = None,
                 ):
    if view_filter is not None:
        view_filter = enums.ViewType.get(view_filter)
    if related_type is not None:
        related_type = enums.ItemType.get(related_type)
    item_type = enums.ItemType.get(item_type)

    parent_model = None

    db_msg, db_model = item_type._msg_and_model(
        (enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Grouping))

    if related_type:
        parent_model = db_model
        db_msg, db_model = related_type._msg_and_model(
            (enums.ItemType.Gallery, enums.ItemType.Page))

        col = db.relationship_column(parent_model, db_model)
        if not col:
            raise exceptions.APIError(
                utils.this_function(),
                "{} has no relationship with {}".format(
                    related_type,
                    item_type))

        if item_id is None:
            raise exceptions.APIError(utils.this_function(), "Missing id of parent item")

    model_ids = None
    if not db_model == db.Page:
        model_ids = search_cmd.ModelFilter().run(db_model, search_query)

    filter_op = None
    join_exp = None
    metatag_name = None
    if view_filter == enums.ViewType.Favorite:
        metatag_name = db.MetaTag.names.favorite
    elif view_filter == enums.ViewType.Inbox:
        metatag_name = db.MetaTag.names.inbox

    if metatag_name:
        if hasattr(db_model, "metatags"):
            filter_op = db.MetaTag.name == metatag_name
            join_exp = db_model.metatags
    elif view_filter == enums.ViewType.Library:
        if hasattr(db_model, "metatags"):
            filter_op = ~db_model.metatags.any(db.MetaTag.name == db.MetaTag.names.inbox)

    if related_type:
        related_filter = parent_model.id == item_id
        filter_op = db.and_op(filter_op, related_filter) if filter_op is not None else related_filter
        join_exp = [col, join_exp] if join_exp is not None else col

    print("########################", db_model)
    return view_filter, item_type, db_msg, db_model, model_ids, filter_op, join_exp, metatag_name


def library_view(item_type: enums.ItemType = enums.ItemType.Gallery,
                 item_id: int = None,
                 related_type: enums.ItemType = None,
                 page: int = 0,
                 limit: int = 100,
                 sort_by: str = "",
                 search_query: str = "",
                 filter_id: int = None,
                 view_filter: enums.ViewType = enums.ViewType.Library):
    """
    Fetch items from the database.
    Provides pagination.

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Collection`, :py:attr:`.ItemType.Grouping`
        page: current page (zero-indexed)
        sort_by: name of column to order by ...
        limit: amount of items per page
        search_query: filter item by search terms
        filter_id: current filter list id
        view_filter: type of view, set ``None`` to not apply any filter
        related_type: child item
        item_id: id of parent item

    Returns:
        .. code-block:: guess

            [
                item message object,
                ...
            ]
    """
    view_filter, item_type, db_msg, db_model, model_ids, filter_op, join_exp, metatag_name = _view_helper(
        item_type, search_query, filter_id, view_filter, item_id, related_type)

    items = message.List(db_model.__name__.lower(), db_msg)

    [items.append(db_msg(x)) for x in database_cmd.GetModelItemByID().run(
        db_model, model_ids, limit=limit, offset=page * limit, filter=filter_op, join=join_exp)]

    return items


def get_view_count(item_type: enums.ItemType=enums.ItemType.Gallery,
                   item_id: int = None,
                   related_type: enums.ItemType = None,
                   search_query: str = "",
                   filter_id: int = None,
                   view_filter: enums.ViewType = enums.ViewType.Library):
    """
    Get count of items in view

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Collection`, :py:attr:`.ItemType.Grouping`
        search_query: filter item by search terms
        filter_id: current filter list id
        view_filter: type of view, set ``None`` to not apply any filter
        related_type: child item
        item_id: id of parent item

    Returns:
        .. code-block:: guess

            {
                'count' : int
            }
    """
    view_filter, item_type, db_msg, db_model, model_ids, filter_op, join_exp, metatag_name = _view_helper(
        item_type, search_query, filter_id, view_filter, item_id, related_type)

    return message.Identity('count', {'count': database_cmd.GetModelItemByID().run(
        db_model, model_ids, filter=filter_op, join=join_exp, count=True)})


def translate(t_id: str, locale: str = None, default: str = None):
    """
    Get a translation by translation id. Raises error if no translation was found.

    Args:
        t_id: translation id
        locale: locale to get translations from (will override default locale)
        default: default text when no translation was found

    Returns:
        string
    """
    kwargs = {}
    if locale:
        kwargs["locale"] = locale.lower()
    if default:
        kwargs["default"] = default
    try:
        trs = i18n.t(t_id, **kwargs)
    except KeyError as e:
        raise exceptions.APIError(utils.this_function(), "Translation id '{}' not found".format(t_id))
    except i18n.loaders.loader.I18nFileLoadError as e:
        if default is None:
            log.exception("Failed to load translation file '{}' with key '{}'".format(
                locale if locale else config.translation_locale.value, t_id))
            raise exceptions.APIError(utils.this_function(), "Failed to load translation file: {}".format(e.args))
        trs = default
    return message.Identity("translation", trs)
