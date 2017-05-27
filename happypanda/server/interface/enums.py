from happypanda.common import utils


class GalleryFilter(utils.APIEnum):
    #: Library
    Library = 0
    #: Favourite
    Favorite = 1
    #: Inbox
    Inbox = 2


class ItemType(utils.APIEnum):
    #: Gallery
    Gallery = 0
    #: Collection
    Collection = 1
    #: GalleryList
    GalleryList = 2
    #: Page
    Page = 3
    #: Grouping
    Grouping = 4


class ImageSize(utils.APIEnum):
    #: Original
    Original = 0
    #: Big
    Big = 400
    #: Medium
    Medium = 250
    #: Small
    Small = 100
