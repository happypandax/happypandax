from happypanda.common import constants

class HPlugin:

    ID = "9fb4ce2a-fe47-42ef-8c58-e039d999eb19"
    NAME = "Core"
    AUTHOR = "Pewpew"
    DESCRIPTION = "A Core plugin"
    VERSION = constants.version
    WEBSITE = "https://github.com/Pewpews/happypandax"

    def __init__(self, *args, **kwargs):

        ## Gallery IO
        self.create_hook("on_gallery_from_path") # GalleryFS
        self.create_hook("on_gallery_name_parse")
