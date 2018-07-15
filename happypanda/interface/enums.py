"""
Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These enums are a subclass of the standard :class:`enum.Enum` class.
To retrieve one of these enums see the :ref:`Plugin Interface <interface>`.

Client
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Through the client API, enums can be used by their member names and values interchangeably.
Enum member names are case insensitive::

    ItemType.Gallery == 1 # true
    ItemType.Gallery == ItemType.gaLLeRy # true

It is recommended that enum members are used by their *values* and not names.
Enum member names may change sometime in the future. It is not likely to happen but no promises.

"""

import enum

from happypanda.common import utils, exceptions
from happypanda import core
from happypanda.core import db


class _APIEnum(enum.Enum):
    "A conv. enum class"

    @classmethod
    def get(cls, key):

        # for some ungodly unknown reason this check wouldnt work when calling from the client
        # so i ended up comparing strings instead
        if repr(type(key)) == repr(cls):
            return key
        if key is not None:
            try:
                return cls[key]
            except KeyError:
                pass

            try:
                return cls(key)
            except ValueError:
                pass

            if isinstance(key, str):
                low_key = key.lower()
                for name, member in cls.__members__.items():
                    if name.lower() == low_key:
                        return member

        raise exceptions.EnumError(
            utils.this_function(),
            "{}: enum member doesn't exist '{}'".format(
                cls.__name__,
                repr(key)))


class ViewType(_APIEnum):
    #: Contains all items except items in Trash
    All = 6
    #: Contains all items except items in Inbox and Trash
    Library = 1
    #: Contains all favourite items (mutually exclusive with items in Inbox)
    Favorite = 2
    #: Contains only items in Inbox
    Inbox = 3
    #: Contains only items in Trash
    Trash = 4
    #: Contains only items in ReadLater
    ReadLater = 5


class TemporaryViewType(_APIEnum):
    #: Contains gallery items to be added
    GalleryAddition = 1


class ItemType(_APIEnum):
    #: Gallery
    Gallery = 1
    #: Collection
    Collection = 2
    #: GalleryFilter
    GalleryFilter = 3
    #: Page
    Page = 4
    #: Gallery Namespace
    Grouping = 5
    #: Gallery Title
    Title = 6
    #: Gallery Artist
    Artist = 7
    #: Category
    Category = 8
    #: Language
    Language = 9
    #: Status
    Status = 10
    #: Circle
    Circle = 11
    #: URL
    Url = 12
    #: Gallery Parody
    Parody = 13

    def _msg_and_model(item_type, allowed=tuple(), error=True):
        """
        Get the equivalent Message and Database object classes for ItemType member

        Args:
            allowed: a tuple of ItemType members which are allowed, empty tuple for all members
            error: raise error if equivalent is not found, else return generic message object class
        """
        if allowed and repr(item_type) not in (repr(x) for x in allowed):
            raise exceptions.APIError(
                utils.this_function(),
                "ItemType must be on of {} not '{}'".format(
                    allowed,
                    repr(item_type)))

        db_model = None
        try:
            db_model = getattr(db, item_type.name)
        except AttributeError:
            if error:
                raise exceptions.CoreError(utils.this_function(),
                                           "Equivalent database object class for {} was not found".format(item_type))

        obj = None
        try:
            obj = getattr(core.message, item_type.name)
        except AttributeError:
            try:
                if db_model and issubclass(db_model, db.NameMixin):
                    obj = getattr(core.message, db.NameMixin.__name__)
            except AttributeError:
                pass
            if not obj:
                if error:
                    raise exceptions.CoreError(utils.this_function(),
                                               "Equivalent Message object class for {} was not found".format(item_type))
                obj = core.message.DatabaseMessage

        return obj, db_model


class ImageSize(_APIEnum):
    #: Original image size
    Original = 1
    #: Big image size
    Big = 2
    #: Medium image size
    Medium = 3
    #: Small image size
    Small = 4


class ServerCommand(_APIEnum):
    #: Shut down the server
    ServerQuit = 1

    #: Restart the server
    ServerRestart = 2

    #: Request authentication
    RequestAuth = 3


class ItemSort(_APIEnum):

    #: Gallery Random
    GalleryRandom = 1
    #: Gallery Title
    GalleryTitle = 2
    #: Gallery Artist Name
    GalleryArtist = 3
    #: Gallery Date Added
    GalleryDate = 4
    #: Gallery Date Published
    GalleryPublished = 5
    #: Gallery Last Read
    GalleryRead = 6
    #: Gallery Last Updated
    GalleryUpdated = 7
    #: Gallery Rating
    GalleryRating = 8
    #: Gallery Read Count
    GalleryReadCount = 9
    #: Gallery Page Count
    GalleryPageCount = 10

    #: Artist Name
    ArtistName = 20

    #: Namespace
    NamespaceTagNamespace = 30
    #: Tag
    NamespaceTagTag = 31

    #: Circle Name
    CircleName = 40

    #: Parody Name
    ParodyName = 45

    #: Collection Random
    CollectionRandom = 50
    #: Collection Name
    CollectionName = 51
    #: Collection Date Added
    CollectionDate = 52
    #: Collection Date Published
    CollectionPublished = 53
    #: Collection Gallery Count
    CollectionGalleryCount = 54


class ProgressType(_APIEnum):

    #: Unknown
    Unknown = 1
    #: Network request
    Request = 2
    #: A check for new update
    CheckUpdate = 3
    #: Updating application
    UpdateApplication = 4
    #: Scanning for galleries
    GalleryScan = 5
    #: Adding items to the database
    ItemAdd = 6
    #: Removing items from the database
    ItemRemove = 7


class PluginState(_APIEnum):

    #: Puporsely disabled
    Disabled = 0
    #: Unloaded because of dependencies, etc.
    Unloaded = 1
    #: Was just registered but not installed
    Registered = 2
    #: Allowed to be enabled
    Installed = 3
    #: Plugin is loaded and in use
    Enabled = 4
    #: Failed because of error
    Failed = 5


class CommandState(_APIEnum):

    #: command has not been put in any service yet
    out_of_service = 0

    #: command has been put in a service (but not started or stopped yet)
    in_service = 1

    #: command has been scheduled to start
    in_queue = 2

    #: command has been started
    started = 3

    #: command has finished succesfully
    finished = 4

    #: command has been forcefully stopped without finishing
    stopped = 5

    #: command has finished with an error
    failed = 6
