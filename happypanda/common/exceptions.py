"""
These are errors that HPX may raise.
Any error raised not on this list is an *unhandled exception* and usually classifies as a critical error.

.. exec::

    from happypanda.common import exceptions
    import inspect

    for name, obj in sorted(inspect.getmembers(exceptions, inspect.isclass), key=lambda a:a[1].code):
        if issubclass(obj, exceptions.HappypandaError):
            print(".. autoexception:: {}.{}".format(obj.__module__, obj.__name__))

"""
from happypanda.common import hlogger

log = hlogger.Logger(__name__)

_error_codes = []


def _error_code(code):
    assert isinstance(code, int), "Error code must be of type int"
    assert code not in _error_codes, "Error code already used"
    _error_codes.append(code)

    def wrap(cls):
        cls.code = code
        cls.name = cls.__name__
        d = '**Code**: ``{}``\n\n'.format(code)
        if cls.__doc__ is not None:
            cls.__doc__ = d + cls.__doc__
        else:
            cls.__doc__ = d

        return cls
    return wrap


@_error_code(100)
class HappypandaError(RuntimeError):
    """Base Happypanda exception, all exceptions will derive from this."""

    def __init__(self, msg):
        """init func."""
        super().__init__(msg)
        self.msg = "[{}] {}: {}".format(self.code, self.__class__.__name__, msg)

# ## CORE -- CODE: 100+ ##


@_error_code(101)
class CoreError(HappypandaError):
    """Base Happypanda core exception, all core exceptions will derive from this.

    Args:
        where: where the error occured
        message: explanation of error
    """

    def __init__(self, where, message):
        """init func."""
        super().__init__(message)
        self.where = where
        self.msg = message


@_error_code(102)
class TimeoutError(CoreError):
    """
    Timed out
    """
    pass


@_error_code(110)
class SettingsError(CoreError):
    """
    Base settings error
    """
    pass


@_error_code(120)
class CommandError(CoreError):
    """
    Base command error
    """
    pass


@_error_code(121)
class CommandAlreadyRunningError(CoreError):
    """
    Command is already running
    """

    pass

    # ## PLUGINS -- CODE: 200+ ##


@_error_code(200)
class PluginError(CoreError):
    """Base plugin exception, all plugin exceptions will derive from this.

    Args:
        name: name of plugin
        message: explanation of error
    """

    def __init__(self, name_or_node, message):
        """init func."""

        self.node = None
        if isinstance(name_or_node, str):
            name = name_or_node
        else:
            name = name_or_node.info.shortname
            self.node = name_or_node

        super().__init__(name, message)


@_error_code(201)
class PluginAttributeError(PluginError, AttributeError):
    """Plugin Attribute Error."""

    pass


@_error_code(202)
class PluginCommandError(PluginError):
    """Plugin Command Error."""

    pass


@_error_code(203)
class PluginCommandNotFoundError(PluginCommandError):
    """Plugin Command Not Found Error."""
    pass


@_error_code(204)
class PluginHandlerError(PluginError):
    """Plugin Handler Error."""

    pass


@_error_code(205)
class PluginSignatureError(PluginError):
    """Plugin Signature Error."""
    pass


@_error_code(206)
class PluginLoadError(PluginError):
    """Plugin Load Error."""
    pass


@_error_code(207)
class PluginInitError(PluginError):
    """Plugin Init Error."""
    pass

    # ## DATABASE -- CODE: 300+ ##


@_error_code(300)
class DatabaseError(CoreError):
    """Base database exception, all database exceptions will derive from this."""

    pass


@_error_code(301)
class DatabaseInitError(DatabaseError):
    """Database initialization error."""

    def __init__(self, msg):
        """init func."""
        super().__init__("database initiation", "An error occured in the database initialization process: " + msg)


@_error_code(302)
class DatabaseVersionError(DatabaseError):
    """Database version error."""

    def __init__(self, msg):
        """init func."""
        super().__init__("database initiation", "Database version mismatch: " + msg)


@_error_code(303)
class DatabaseItemNotFoundError(DatabaseError):
    """Database item not found error"""
    pass

    # ## SERVER -- CODE: 400+ ##


@_error_code(400)
class ServerError(CoreError):
    """Base server exception, all server exceptions will derive from this."""

    pass


@_error_code(401)
class ClientDisconnectError(ServerError):
    """Client disconnected."""

    pass


@_error_code(403)
class InvalidMessage(ServerError):
    """Invalid message error."""

    pass


@_error_code(404)
class APIError(ServerError):
    """API error."""

    pass


@_error_code(405)
class APIRequirementError(ServerError):
    """API requirement error."""

    pass


@_error_code(406)
class AuthError(ServerError):
    """Auth Base Error."""

    def __init__(self, where, msg):
        super().__init__(where, msg)


@_error_code(407)
class AuthRequiredError(AuthError):

    def __init__(self, where, msg):
        super().__init__(where, msg)


@_error_code(408)
class SessionExpiredError(ServerError):
    """Session expired error."""

    def __init__(self, where, session_id):
        super().__init__(where, "Session '{}' has expired".format(session_id))


@_error_code(409)
class EnumError(ServerError):
    """Enum error."""
    pass


@_error_code(410)
class ParsingError(ServerError):
    ""
    pass


@_error_code(411)
class AuthWrongCredentialsError(AuthError):
    ""

    def __init__(self, where, msg):
        super().__init__(where, msg)


@_error_code(412)
class AuthMissingCredentials(AuthError):
    ""

    def __init__(self, where, msg):
        super().__init__(where, msg)

    # ## CLIENT -- CODE: 500+ ##


@_error_code(500)
class ClientError(ServerError):
    """Base client exception, all client exceptions will derive from this.

    Args:
        name: name of client
        msg: error message
    """

    def __init__(self, name, msg):
        """init func."""
        try:
            super().__init__("An error occured in client '{}':\t{} ".format(name, msg))
        except BaseException:
            super().__init__(name, "An error occured in client :\t{} ".format(msg))


@_error_code(501)
class ConnectionError(ClientError):
    """Server connection error."""

    pass


@_error_code(502)
class ServerDisconnectError(ConnectionError):
    """Server disconnected."""

    pass

    ## ARCHIVE -- CODE: 600+ ##


@_error_code(600)
class ArchiveError(CoreError):
    """Base archive exception, all archive exceptions will derive from this
    """
    pass


@_error_code(601)
class ArchiveCreateError(ArchiveError):
    "Could not create archive object"

    def __init__(self, filepath, error):
        return super().__init__(
            "Failed creating archive object ({}):{}".format(
                error, filepath))


@_error_code(602)
class ArchiveCorruptError(ArchiveError):
    "Bad file found in archive"

    def __init__(self, filepath):
        return super().__init__("Bad file found in archive: '{}'".format(filepath))


@_error_code(603)
class ArchiveFileNotFoundError(ArchiveError):
    "File not found in archive"

    def __init__(self, f, archive_f):
        return super().__init__("File '{}' not found in archive: '{}'".format(f, archive_f))


@_error_code(604)
class ArchiveUnsupportedError(ArchiveError):
    "Unsupported archive"

    def __init__(self, f):
        return super().__init__("Archive file '{}' is not supported".format(f))


@_error_code(605)
class ArchiveExtractError(ArchiveError):
    "Archive extraction error"
    pass


@_error_code(606)
class ArchiveExistError(ArchiveError):
    "Archive does not exist error"

    def __init__(self, f):
        return super().__init__("Archive file does not exist. File '{}' not found".format(f))


@_error_code(607)
class NotAnArchiveError(ArchiveError):
    "Not an archive"

    def __init__(self, f):
        return super().__init__("Path is not an archive: {}".format(f))

    ## NETWORK -- CODE: 700+ ##


@_error_code(700)
class NetworkError(CoreError):
    """
    Base network exception, all network exceptions will derive from this
    """

    def __init__(self, message, properties=None):
        if properties:
            pass
        # TODO: urls and stuff
        return super().__init__("network", message)

    ## ETC.  -- CODE:900+ ##


@_error_code(900)
class JSONParseError(ServerError):
    """JSON parse error."""

    def __init__(self, json_data, name, msg):
        super().__init__("Client ''".format(name), msg)
        # TODO: log data?
