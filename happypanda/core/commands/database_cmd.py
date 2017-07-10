from happypanda.common import utils, hlogger, exceptions, constants
from happypanda.core.command import Command, CommandEvent, AsyncCommand, CommandEntry
from happypanda.core.commands import io_cmd
from happypanda.core import db, services
from happypanda.interface import enums

import time

log = hlogger.Logger(__name__)


class GetModelCover(AsyncCommand):
    """
    Fetch a database model item's cover

    By default, the following models are supported

    - Gallery
    - Page
    - Grouping
    - Collection
    - GalleryFilter

    Returns a Profile database item
    """

    models = CommandEntry("models", tuple)

    def __init__(self, service=None):
        super().__init__(service)
        self.model = None
        self.cover = None
        self._supported_models = set()

    @models.default()
    def _models():
        return (
            db.Grouping,
            db.Collection,
            db.Gallery,
            db.Page,
            db.GalleryFilter
        )

    def main(self, model: db.Base, item_id: int,
             image_size: enums.ImageSize) -> db.Profile:

        self.model = model

        with self.models.call() as plg:
            for p in plg.all(default=True):
                self._supported_models.update(p)

        if self.model not in self._supported_models:
            raise exceptions.CommandError(
                utils.this_command(self),
                "Model '{}' is not supported".format(model))

        img_hash = io_cmd.ImageItem.gen_hash(
            model, image_size.value, item_id)

        sess = constants.db_session()
        self.cover = sess.query(db.Profile).filter(
            db.Profile.data == img_hash).one_or_none()

        if not self.cover:
            self.cover = db.Profile()

            related_models = db.related_classes(model)
            if db.Page in related_models:
                page = sess.query(
                    db.Page.path).filter(
                    db.Page.number == 1).one_or_none()
                if page:
                    im_props = io_cmd.ImageProperties(
                        image_size, 0, constants.dir_thumbs)
                    self.cover.path = io_cmd.ImageItem(
                        self.service, page[0], im_props).main()
                else:
                    return None

            else:
                raise NotImplementedError

            self.cover.data = img_hash
            self.cover.size = str(tuple(image_size.value))

            item_id.profiles.append(self.cover)
            sess.commit()

        return self.cover


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


class GetModelItemByID(Command):
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

        id_amount = len(ids)
        # TODO: only SQLite has 999 variables limit
        _max_variables = 900
        if id_amount > _max_variables:
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

        elif id_amount == 1:
            self.fetched_items = (q.get(ids.pop()),)
        else:
            q = q.filter(model.id.in_(ids))
            self.fetched_items = tuple(self._query(q, limit, offset))

        self.fetched.emit(db.model_name(model), self.fetched_items)

        return self.fetched_items
