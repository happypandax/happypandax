from happypanda.common import utils, hlogger, exceptions, constants
from happypanda.server.core.command import Command, CommandEvent
from happypanda.server.core import db

log = hlogger.Logger(__name__)


class GetModelClass(Command):
    """
    Returns a database model by name
    """

    def __init__(self):
        super().__init__()

    def main(self, model_name: str) -> db.Base:

        if not hasattr(db, model_name):
            raise exceptions.CoreError(
                utils.this_command(self),
                "No database model named '{}'".format(model_name))

        return getattr(db, model_name)


class GetSession(Command):
    """
    Returns a database session
    """

    def __init__(self):
        super().__init__()

    def main(self) -> db.scoped_session:
        return constants.db_session()


class GetModelByID(Command):
    """
    Fetch model items from the database by a set of ids

    Returns a tuple of model items
    """

    fetched = CommandEvent("fetched", str, tuple)

    def __init__(self):
        super().__init__()

        self.fetched_items = tuple()

    def _query(self, q, limit, offset):
        if offset:
            q = q.offset(offset)

        return q.limit(limit).all()

    def main(self, model: db.Base, ids: set, limit: int = 999,
             filter: str = "", order_by: str = "", offset: int = 0) -> tuple:

        log.d("Fetching items from a set with", len(ids), "ids")

        s = constants.db_session()

        q = s.query(model)

        if filter:
            q = q.filter(db.sa_text(filter))

        if order_by:
            q = q.order_by(db.sa_text(order_by))

        # TODO: only SQLite has 999 variables limit
        _max_variables = 900
        if len(ids) > _max_variables:
            ids_list = list(ids)
            fetched_list = []
            queries = []

            while len(ids_list):
                queries.append(
                    q.filter(model.id.in_(ids_list[:_max_variables])))
                ids_list = ids_list[_max_variables:]

            for x in queries:
                limit = limit - len(fetched_list)
                if limit <= 0:
                    break

                fetched_list.extend(self._query(x, limit, offset))

            self.fetched_items = tuple(fetched_list)

        else:
            q = q.filter(model.id.in_(ids))
            self.fetched_items = tuple(self._query(q, limit, offset))

        self.fetched.emit(db.model_name(model), self.fetched_items)

        return self.fetched_items
