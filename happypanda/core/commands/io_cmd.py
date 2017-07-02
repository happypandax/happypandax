from happypanda.common import utils, hlogger, exceptions, constants
from happypanda.core.command import AsyncCommand, CommandEvent, CommandEntry
from happypanda.core.commands import database_cmd
from happypanda.core import services, db
from happypanda.interface import enums


from PIL import Image

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

    def __init__(self, service=services.ImageService.generic):
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

    def main(self, model: db.Base, item_id: int, image_size: enums.ImageSize) -> db.Profile:
        
        self.model = model

        with self.models.call() as plg:
            for p in plg.all(default=True):
                self._supported_models.update(p)

        if self.model not in self._supported_models:
            raise exceptions.CommandError(
                utils.this_command(self),
                "Model '{}' is not supported".format(model))

        img_hash = services.ImageItem.gen_hash(model, image_size.value, item_id)

        sess = constants.db_session()
        self.cover = sess.query(db.Profile).filter(db.Profile.data == img_hash).one_or_none()

        if not self.cover:
            self.cover = db.Profile()
            
            related_models = db.related_classes(model)
            if db.Page in related_models:
                page = sess.query(db.Page.path).filter(db.Page.number == 1).one_or_none()
                if page:
                    im_props = services.ImageProperties(image_size, 0, constants.dir_thumbs)
                    self.cover.path = services.ImageItem(self.service, page, im_props).main()
                else:
                    return None

            else:
                raise NotImplementedError

            self.cover.data = img_hash
            self.cover.size = str(tuple(image_size.value))

            item_id.profiles.append(self.cover)
            sess.commit()

        return self.cover

