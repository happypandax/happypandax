from happypanda.common import utils, exceptions, hlogger, config
from happypanda.core import db
from happypanda.interface import enums
from happypanda.core.commands import database_cmd

log = hlogger.Logger(__name__)


def _sort_helper(sort_by, sort_desc, db_model):

    ordering = None
    order_exp = tuple()
    group_exp = tuple()
    join_exp = tuple()

    if sort_by is not None:
        try:
            sort_by = enums.ItemSort.get(sort_by)
            ordering = database_cmd.GetDatabaseSort().run(db_model, sort_by.value)
        except exceptions.EnumError:
            if isinstance(sort_by, int):
                ordering = database_cmd.GetDatabaseSort().run(db_model, sort_by)

            if ordering is None:
                raise exceptions.EnumError(
                    utils.this_function(),
                    "{}: enum member or sort index doesn't exist '{}'".format(
                        enums.ItemSort.__name__,
                        repr(sort_by)))

    if ordering is not None:
        join_exp = ordering.joins
        group_exp = ordering.groupby
        order_exp = ordering.orderby

        if not isinstance(order_exp, (list, tuple)):
            order_exp = (order_exp,)
        if not isinstance(join_exp, (list, tuple)):
            join_exp = (join_exp,)
        if not isinstance(group_exp, (list, tuple)):
            group_exp = (group_exp,)
        if sort_desc:
            order_exp = tuple(db.desc_expr(x) for x in order_exp)

    return order_exp, group_exp, join_exp


def _get_locale(locale=None):
    if locale:
        return locale
    return config.translation_locale.value
