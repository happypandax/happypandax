from happypanda.common import utils, exceptions
from happypanda.core import message, db


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

    def _msg_and_model(item_type, allowed=tuple(), error=True):
        """
        Get the equivalent Message and Database object classes for ItemType member
    
        Args:
            allowed: a tuple of ItemType members which are allowed, empty tuple for all members
            error: raise error if equivalent is not found, else return generic message object class
        """
        if allowed and item_type not in allowed:
            raise exceptions.APIError("ItemType must be on of {}".format(allowed))

        obj = None
        try:
            obj = getattr(message, item_type.name)
        except AttributeError:
            if error:
                raise exceptions.CoreError(utils.this_function(), "Equivalent Message object class for {} was not found".format(item_type))
            obj = DatabaseMessage

        db_model = None
        try:
            db_model = getattr(db, item_type.name)
        except AttributeError:
            if error:
                raise exceptions.CoreError(utils.this_function(), "Equivalent database object class for {} was not found".format(item_type))
        return obj, db_model


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
