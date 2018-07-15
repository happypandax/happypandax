"""
UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import i18n
import itertools

from collections import OrderedDict

from happypanda.common import utils, exceptions, hlogger, config, constants
from happypanda.core import message, db, services
from happypanda.interface import enums, helpers
from happypanda.core.commands import database_cmd, search_cmd

log = hlogger.Logger(__name__)


def _view_helper(item_type: enums.ItemType=enums.ItemType.Gallery,
                 search_query: str = "",
                 filter_id: int = None,
                 view_filter: enums.ViewType = enums.ViewType.Library,
                 item_id: int = None,
                 related_type: enums.ItemType = None,
                 search_options: dict = {},
                 ):
    if view_filter is not None:
        view_filter = enums.ViewType.get(view_filter)
    if related_type is not None:
        related_type = enums.ItemType.get(related_type)
    item_type = enums.ItemType.get(item_type)

    if search_options:
        search_option_names = [x.name for x in search_cmd._get_search_options()]
        for n in search_options:
            if n not in search_option_names:
                raise exceptions.APIError(utils.this_function(), "Invalid search option name '{}'".format(n))

    filter_op = []
    join_exp = []
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

    if filter_id:
        if db_model != db.Gallery:
            g_col = db.relationship_column(db_model, db.Gallery)
            if not g_col:
                raise exceptions.APIError(
                    utils.this_function(),
                    "Cannot use {} because {} has no relationship with {}".format(
                        enums.ItemType.GalleryFilter,
                        related_type if related_type else item_type,
                        enums.ItemType.Gallery))
            join_exp.append(g_col)
        join_exp.append(db.relationship_column(db.Gallery, db.GalleryFilter))
        filter_op.append(db.GalleryFilter.id == filter_id)

    model_ids = None
    if not db_model == db.Page:
        model_ids = search_cmd.ModelFilter().run(db_model, search_query, search_options)

    metatag_name = None
    if view_filter == enums.ViewType.Favorite:
        metatag_name = db.MetaTag.names.favorite
    elif view_filter == enums.ViewType.Inbox:
        metatag_name = db.MetaTag.names.inbox
    elif view_filter == enums.ViewType.Trash:
        metatag_name = db.MetaTag.names.trash

    if metatag_name:
        if hasattr(db_model, "metatags"):
            filter_op.append(db.MetaTag.name == metatag_name)
            join_exp.append(db_model.metatags)
    elif view_filter == enums.ViewType.Library:
        if hasattr(db_model, "metatags"):
            filter_op.append(~db_model.metatags.any(db.MetaTag.name == db.MetaTag.names.inbox))
            filter_op.append(~db_model.metatags.any(db.MetaTag.name == db.MetaTag.names.trash))
    elif view_filter == enums.ViewType.All:
        if hasattr(db_model, "metatags"):
            filter_op.append(~db_model.metatags.any(db.MetaTag.name == db.MetaTag.names.trash))

    if related_type:
        filter_op.append(parent_model.id == item_id)
        join_exp.append(col)

    if len(filter_op) > 1:
        filter_op = db.and_op(*filter_op)
    elif filter_op:
        filter_op = filter_op[0]
    else:
        filter_op = None

    return view_filter, item_type, db_msg, db_model, model_ids, filter_op, join_exp, metatag_name


def library_view(item_type: enums.ItemType = enums.ItemType.Gallery,
                 item_id: int = None,
                 related_type: enums.ItemType = None,
                 page: int = 0,
                 limit: int = 100,
                 sort_by: enums.ItemSort = None,
                 sort_desc: bool=False,
                 search_query: str = "",
                 search_options: dict = {},
                 filter_id: int = None,
                 view_filter: enums.ViewType = enums.ViewType.Library):
    """
    Fetch items from the database.
    Provides pagination.

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Collection`, :py:attr:`.ItemType.Grouping`
        page: current page (zero-indexed)
        sort_by: either a :py:class:`.ItemSort` or a sort index
        sort_desc: order descending (default is ascending)
        limit: amount of items per page
        search_query: filter item by search terms
        search_options: options to apply when filtering, see :ref:`Settings` for available search options
        filter_id: current :py:attr:`.ItemType.GalleryFilter` item id
        view_filter: type of view, set ``None`` to not apply any filter
        related_type: child item
        item_id: id of parent item

    Returns:
        .. code-block:: guess

            [
                item message object,
                ...
            ]

    .. seealso::

        :func:`.get_sort_indexes`
    """
    view_filter, item_type, db_msg, db_model, model_ids, filter_op, join_exp, metatag_name = _view_helper(
        item_type, search_query, filter_id, view_filter, item_id, related_type, search_options)

    items = message.List(db_model.__name__.lower(), db_msg)

    order_exp, group_exp, sort_joins = helpers._sort_helper(sort_by, sort_desc, db_model)

    if sort_joins:
        join_exp.extend(sort_joins)
        # need unique but ordered results, cannot use set so we make use with this
        join_exp = tuple(OrderedDict([(x, None) for x in join_exp]).keys())

    [items.append(db_msg(x)) for x in database_cmd.GetModelItems().run(
        db_model, model_ids, limit=limit, offset=page * limit,
        filter=filter_op, join=join_exp, order_by=order_exp, group_by=group_exp)]

    return items


def get_view_count(item_type: enums.ItemType=enums.ItemType.Gallery,
                   item_id: int = None,
                   related_type: enums.ItemType = None,
                   search_query: str = "",
                   search_options: dict = {},
                   filter_id: int = None,
                   view_filter: enums.ViewType = enums.ViewType.Library):
    """
    Get count of items in view

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Collection`, :py:attr:`.ItemType.Grouping`
        search_query: filter item by search terms
        search_options: options to apply when filtering, see :ref:`Settings` for available search options
        filter_id: current :py:attr:`.ItemType.GalleryFilter` item id
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
        item_type, search_query, filter_id, view_filter, item_id, related_type, search_options)

    return message.Identity('count', {'count': database_cmd.GetModelItems().run(
        db_model, model_ids, filter=filter_op, join=join_exp, count=True)})


def translate(t_id: str, locale: str = None, default: str = None, placeholder: str = {}, count: int = None):
    """
    Get a translation by translation id.
    Raises error if a default value was not provided and no translation was found.

    You can find more about translations :ref:`here <Translations>`.

    Args:
        t_id: translation id
        locale: locale to get translations from (will override default locale)
        default: default text when no translation was found
        placeholder: ?
        count: pluralization

    Returns:
        string

    .. seealso::

        :func:`.get_locales`
    """
    kwargs = {}
    trs = default

    kwargs["locale"] = helpers._get_locale(locale).lower()

    if placeholder:
        kwargs.update(placeholder),
    if count is not None:
        kwargs["count"] = count
    if default:
        kwargs["default"] = default

    if not t_id and default is None:
        raise exceptions.APIError(utils.this_function(), "Invalid translation id: {}".format(t_id))
    elif t_id:
        try:
            trs = i18n.t(t_id, **kwargs)
        except KeyError as e:
            if default is None:
                raise exceptions.APIError(utils.this_function(), "Translation id '{}' not found".format(t_id))

        except i18n.loaders.loader.I18nFileLoadError as e:
            if default is None:
                log.exception("Failed to load translation file '{}' with key '{}'".format(
                    locale if locale else config.translation_locale.value, t_id))
                raise exceptions.APIError(utils.this_function(), "Failed to load translation file: {}".format(e.args))
    return message.Identity("translation", trs)


def get_translations(locale: str = None):
    """
    Get all translations for given locale

    You can find more about translations :ref:`here <Translations>`.

    Args:
        locale: locale to get translations from (will override default locale)

    Returns:
        .. code-block:: guess

            {
                'namespace.translation_id' : string
            }

    .. seealso::

        :func:`.get_locales`
    """
    trs = {}
    locale = helpers._get_locale(locale).lower()
    container = i18n.translations.container
    if locale in container:
        trs = container[locale].copy()
    else:
        try:
            translate("general.locale")
            trs = container[locale].copy()
        except exceptions.APIError:
            pass
    return message.Identity("translations", trs)


def get_sort_indexes(item_type: enums.ItemType=None, translate: bool=True, locale: str=None):
    """
    Get a list of available sort item indexes and names

    Args:
        item_type: return applicable indexes for a specific item type
        translate: translate the sort expression name
        locale: locale to get translations from (will override default locale)

    Returns:
        .. code-block:: guess

            [
                {
                    'index' : int,
                    'name': str,
                    'item_type': int value of :py:class:`.ItemType`
                },
                ...
            ]
    """
    db_sort = database_cmd.GetDatabaseSort()
    if item_type:
        item_type = enums.ItemType.get(item_type)
        items = [item_type]
    else:
        items = list(enums.ItemType)

    sort_indexes = message.List("indexes", dict)
    for i in items:
        _, db_model = i._msg_and_model()
        for idx, name in db_sort.run(db_model, name=True).items():
            if translate:
                try:
                    name = i18n.t("general.sort-idx-{}".format(idx), default=name, locale=helpers._get_locale(locale))
                except Exception:
                    pass
            sort_indexes.append({
                'index': int(idx),
                'name': name,
                'item_type': i.value
            })
    return sort_indexes


def temporary_view(view_type: enums.TemporaryViewType = enums.TemporaryViewType.GalleryAddition,
                   view_id: int = None,
                   limit: int = 100,
                   offset: int = 0,
                   # sort_by: enums.ItemSort = None,
                   # sort_desc: bool=False,
                   ):
    """
    not ready yet...

    Args:
        view_type: type of temporary view
        view_id: id of a specific view
        limit: amount of items per page
        offset: offset the results by n items

    Returns:
        .. code-block:: guess

            {
                'items': [
                        ...
                    ],
                'count': int # count of all items in view
            }
    """
    view_type = enums.TemporaryViewType.get(view_type)
    d = {'items': [], 'count': 0}
    msg_obj = None

    sess = constants.db_session()
    sess.autoflush = False

    if view_type == enums.TemporaryViewType.GalleryAddition:
        msg_obj = message.GalleryFS
        c = constants.store.galleryfs_addition.get({})
        if view_id:
            c = list(c.get(view_id, tuple()))
        else:
            c = list(itertools.chain(*c.values()))

    d['count'] = len(c)
    d['items'] = [msg_obj(x).json_friendly(False) if msg_obj else x for x in c[offset:offset + limit]]

    return message.Identity('items', d)


def submit_temporary_view(view_type: enums.TemporaryViewType = enums.TemporaryViewType.GalleryAddition,
                          view_id: int = None,):
    """
    not ready yet...

    Args:
        view_type: type of temporary view
        view_id: id of a specific view
    Returns:
        []

    |async command|

    """
    view_type = enums.TemporaryViewType.get(view_type)

    cmd_id = None

    if view_type == enums.TemporaryViewType.GalleryAddition:
        c = constants.store.galleryfs_addition.get({})
        if view_id:
            c = list(c.get(view_id, tuple()))
        else:
            c = list(itertools.chain(*c.values()))
        cmd_id = database_cmd.AddItem(services.AsyncService.generic).run(c)

    return message.Identity('command_id', cmd_id)
