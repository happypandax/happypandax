import i18n

from happypanda.common import utils, constants
from happypanda.core import message
from happypanda.interface import enums
from happypanda.core.commands import database_cmd, search_cmd


i18n.load_path.append(constants.dir_translations)
i18n.set("file_format", "yaml")
i18n.set("locale", constants.translation_locale)
i18n.set("fallback", constants.translation_locale)
i18n.set("filename_format", "{locale}.{namespace}.{format}")


def library_view(item_type: enums.ItemType = enums.ItemType.Gallery,
                 page: int = 0,
                 limit: int = 100,
                 sort_by: str = "",
                 search_query: str = "",
                 filter_id: int = None,
                 view_filter: enums.ViewType = enums.ViewType.Library,
                 ctx=None):
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
        view_filter: ...

    Returns:
        list of item message objects
    """
    utils.require_context(ctx)
    view_filter = enums.ViewType.get(view_filter)
    item_type = enums.ItemType.get(item_type)

    db_msg, db_model = item_type._msg_and_model(
        (enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Grouping))

    items = message.List(db_model.__name__.lower(), db_msg)

    model_ids = search_cmd.ModelFilter().run(db_model, search_query)

    [items.append(db_msg(x)) for x in database_cmd.GetModelItemByID().run(
        db_model, model_ids, limit=limit, offset=page * limit)]

    return items


def get_view_count(item_type: enums.ItemType=enums.ItemType.Gallery,
                   search_query: str = "",
                   filter_id: int = None,
                   view_filter: enums.ViewType = enums.ViewType.Library):
    """
    Get count of items in view

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Collection`, :py:attr:`.ItemType.Grouping`
        search_query: filter item by search terms
        filter_id: current filter list id
        view_filter: ...

    Returns:
        ```
        { 'count': int }
        ```
    """

    view_filter = enums.ViewType.get(view_filter)
    item_type = enums.ItemType.get(item_type)

    db_msg, db_model = item_type._msg_and_model(
        (enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Grouping))

    model_ids = search_cmd.ModelFilter().run(db_model, search_query)

    return message.Identity('count', {'count': len(model_ids)})


def translate(t_id: str, locale=None, default=None):
    """
    Get a translation by translation id

    Args:
        t_id: translation id
        locale: locale to get translations from (will override default locale)
        default: default text when no translation was found
    """
    kwargs = {}
    if locale:
        kwargs["locale"] = locale
    if default:
        kwargs["default"] = default
    trs = i18n.t(t_id, **kwargs)
    return message.Identity("translation", trs)
