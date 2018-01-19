from collections import OrderedDict

from happypanda.common import utils, exceptions, hlogger, config
from happypanda.core import db
from happypanda.interface import enums
from happypanda.core.commands import database_cmd

log = hlogger.Logger(__name__)

def _sort_helper(sort_by, sort_desc, db_model):

    ordering = None
    order_exp = None
    group_exp = None
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
        join_exp = tuple(ordering.joins)
        group_exp = ordering.groupby
        order_exp = ordering.orderby
        if sort_desc:
            order_exp = db.desc_expr(order_exp)

    return order_exp, group_exp, join_exp