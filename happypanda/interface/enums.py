from happypanda.common import utils


class ViewType(utils.APIEnum):
    #: Library
    Library = 1
    #: Favourite
    Favorite = 2
    #: Inbox
    Inbox = 3


class ItemType(utils.APIEnum):
    #: Gallery
    Gallery = 1
    #: Collection
    Collection = 2
    #: GalleryFilter
    GalleryFilter = 3
    #: Page
    Page = 4
    #: Grouping
    Grouping = 5


class ImageSize(utils.APIEnum):
    #: Original image size
    Original = 1
    #: Big image size
    Big = 2
    #: Medium image size
    Medium = 3
    #: Small image size
    Small = 4


class ServerCommand(utils.APIEnum):
    #: Shut down the server
    ServerQuit = 1

    #: Restart the server
    ServerRestart = 2

    #: Request authentication
    RequestAuth = 3
