from happypanda.common import utils, hlogger, exceptions, constants
from happypanda.core.command import Command, CommandEvent, AsyncCommand, CommandEntry
from happypanda.core.commands import io_cmd
from happypanda.core import db
from happypanda.interface import enums

log = hlogger.Logger(__name__)


class GetModelImage(AsyncCommand):
    """
    Fetch a database model item's image

    By default, the following models are supported

    - Gallery
    - Page
    - Grouping
    - Collection
    - GalleryFilter

    Returns a Profile database item
    """

    models = CommandEntry("models", tuple)
    generate = CommandEntry("generate", str, str, int, utils.ImageSize)

    cover_event = CommandEvent('cover', object)

    def __init__(self, service=None):
        super().__init__(service, priority=constants.Priority.Low)
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

    @generate.default(capture=True)
    def _generate(model, item_id, size, capture=[db.model_name(x) for x in (db.Page, db.Gallery)]):
        im_path = ""
        model = GetModelClass().run(model)

        if model == db.Gallery:
            page = GetSession().run().query(
                db.Page.path).filter(
                db.and_op(
                    db.Page.gallery_id == item_id,
                    db.Page.number == 1)).one_or_none()
        else:
            page = GetSession().run().query(db.Page.path).filter(db.Page.id == item_id).one_or_none()

        if page:
            im_path = page[0]

        if im_path:
            im_props = io_cmd.ImageProperties(size, 0, constants.dir_thumbs)
            im_path = io_cmd.ImageItem(None, im_path, im_props).main()
        return im_path

    def main(self, model: db.Base, item_id: int,
             image_size: enums.ImageSize) -> db.Profile:

        self.model = model

        if image_size == enums.ImageSize.Original:
            image_size = utils.ImageSize(0, 0)
        else:
            image_size = utils.ImageSize(*constants.image_sizes[image_size.name.lower()])

        with self.models.call() as plg:
            for p in plg.all(default=True):
                self._supported_models.update(p)

        if self.model not in self._supported_models:
            raise exceptions.CommandError(
                utils.this_command(self),
                "Model '{}' is not supported".format(model))

        img_hash = io_cmd.ImageItem.gen_hash(
            model, image_size, item_id)

        cover_path = ""
        generate = True
        sess = constants.db_session()
        self.cover = sess.query(db.Profile).filter(
            db.Profile.data == img_hash).one_or_none()

        if self.cover:
            if io_cmd.CoreFS(self.cover.path).exists:
                generate = False
            else:
                cover_path = self.cover.path
        if generate:
            self.cover = self.run_native(self._generate_and_add, img_hash, generate, cover_path, model, item_id, image_size).get()
        self.cover_event.emit(self.cover)
        return self.cover

    def _generate_and_add(self, img_hash, generate, cover_path, model, item_id, image_size):

        sess = constants.db_session()

        model_name = db.model_name(model)

        new = False
        if cover_path:
            self.cover = sess.query(db.Profile).filter(
                db.Profile.data == img_hash).one_or_none()
        else:
            self.cover = db.Profile()
            new = True

        if generate:
            with self.generate.call_capture(model_name, model_name, item_id, image_size) as plg:
                self.cover.path = plg.first()

            self.cover.data = img_hash
            self.cover.size = str(tuple(image_size))

        if self.cover.path and generate:
            if new:
                s = constants.db_session()
                i = s.query(model).get(item_id)
                i.profiles.append(self.cover)
            sess.commit()
        elif not self.cover.path:
            self.cover = None
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
             filter: str = "", order_by: str = "", offset: int = 0, columns=tuple()) -> tuple:

        log.d("Fetching items from a set with", len(ids), "ids", "offset:", offset, "limit:", limit)
        if not ids:
            return tuple()

        s = constants.db_session()
        if columns:
            q = s.query(*columns)
        else:
            q = s.query(model)

        if filter:
            q = q.filter(db.sa_text(filter))

        if order_by:
            q = q.order_by(db.sa_text(order_by))

        id_amount = len(ids)
        # TODO: only SQLite has 999 variables limit
        _max_variables = 900
        if id_amount > _max_variables:
            fetched_list = [x for x in q.all() if x.id in ids]
            fetched_list = fetched_list[offset:][:limit]
            self.fetched_items = tuple(fetched_list)
        elif id_amount == 1:
            self.fetched_items = (q.get(ids.pop()),)
        else:
            q = q.filter(model.id.in_(ids))
            self.fetched_items = tuple(self._query(q, limit, offset))

        self.fetched.emit(db.model_name(model), self.fetched_items)
        log.d("Returning", len(self.fetched_items), "fetched items")
        return self.fetched_items


class GetModelItems(Command):
    """
    Fetch model items from the database

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

    def main(self, model: db.Base, limit: int = 999,
             filter: str = "", order_by: str = "", offset: int = 0) -> tuple:

        s = constants.db_session()

        q = s.query(model)

        if filter:
            q = q.filter(db.sa_text(filter))

        if order_by:
            q = q.order_by(db.sa_text(order_by))

        self.fetched_items = tuple(self._query(q, limit, offset))

        self.fetched.emit(db.model_name(model), self.fetched_items)
        return self.fetched_items
