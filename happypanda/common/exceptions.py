"""exceptions module."""
import logging

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

_error_codes = []
def error_code(code):
    assert isinstance(code, int), "Error code must be of type int"
    assert code not in _error_codes, "Error code already used"
    _error_codes.append(code)
    def wrap(cls):
        cls.code = code
        cls.name = cls.__name__
        return cls
    return wrap

@error_code(100)
class HappypandaError(RuntimeError):
    """Base Happypanda exception, all exceptions will derive from this."""

    def __init__(self, msg):
        """init func."""
        super().__init__(msg)
        self.msg = "[{}]{}: {}".format(self.code, self.__class__.__name__, msg)

    def log(self):
        "log exception"
        from happypanda.common.utils import eprint  # HACK: check if importing from __init__ works
        log_e(self.msg)
        eprint(self.msg)

# ## CORE -- CODE: 100+ ##

@error_code(101)
class CoreError(HappypandaError):
    """Base Happypanda core exception, all core exceptions will derive from this.

    Params:
        where -- where the error occured
        message -- explanation of error
    """

    def __init__(self, where, message):
        """init func."""
        super().__init__(message)
        self.where = where
        self.msg = message


        # ## PLUGINS -- CODE: 200+ ##

@error_code(200)
class PluginError(CoreError):
    """Base plugin exception, all plugin exceptions will derive from this.

    Params:
        name -- name of plugin
        message -- explanation of error
    """

    def __init__(self, name, message):
        """init func."""
        super().__init__("Plugin: " + name, message)


@error_code(201)
class PluginIDError(PluginError):
    """Plugin ID Error."""

    pass


@error_code(202)
class PluginNameError(PluginIDError):
    """Plugin Name Error."""

    pass


@error_code(203)
class PluginMethodError(PluginError, AttributeError):
    """Plugin Method Error."""

    pass


@error_code(204)
class PluginAttributeError(PluginError):
    """Plugin Attribute Error."""

    pass


@error_code(205)
class PluginHookError(PluginError):
    """Plugin Hook Error."""

    pass


@error_code(206)
class PluginHandlerError(PluginError):
    """Plugin Handler Error."""

    pass

    # ## DATABASE -- CODE: 300+ ##

@error_code(300)
class DatabaseError(CoreError):
    """Base database exception, all database exceptions will derive from this."""

    pass

@error_code(301)
class DatabaseInitError(DatabaseError):
    """Database initialization error."""

    def __init__(self, msg):
        """init func."""
        super().__init__("An error occured in the database initialization process: " + msg)

@error_code(302)
class DatabaseVersionError(DatabaseError):
    """Database version error."""

    def __init__(self, msg):
        """init func."""
        super().__init__("Database version mismatch: " + msg)

    # ## SERVER -- CODE: 400+ ##

@error_code(400)
class ServerError(CoreError):
    """Base server exception, all server exceptions will derive from this."""

    pass


@error_code(401)
class ClientDisconnectError(ServerError):
    """Client disconnected."""

    pass

@error_code(403)
class InvalidMessage(ServerError):
    """Invalid message error."""

    pass

@error_code(404)
class APIError(ServerError):
    """API error."""

    pass


    # ## CLIENT -- CODE: 500+ ##

@error_code(500)
class ClientError(ServerError):
    """Base client exception, all client exceptions will derive from this.

    Params:
        name -- name of client
        msg -- error message
    """

    def __init__(self, name, msg):
        """init func."""
        try:
            super().__init__("An error occured in client '{}':\t{} ".format(name, msg))
        except:
            super().__init__(name, "An error occured in client :\t{} ".format(msg))


@error_code(501)
class ServerDisconnectError(ClientError):
    """Server disconnected."""

    pass

    ## ARCHIVE -- CODE: 600+ ##
@error_code(600)
class ArchiveError(HappypandaError):
    """Base archive exception, all acrhive exceptions will derive from this
    """
    pass

@error_code(601)
class CreateArchiveError(ArchiveError):
    "Could not create archive object"
    def __init__(self, filepath, error):
        return super().__init__("Failed creating archive object ({}):{}".format(error, filepath))

@error_code(602)
class BadArchiveError(ArchiveError):
    "Bad file found in archive"
    def __init__(self, filepath):
        return super().__init__("Bad file found in archive:{}".format(filepath))

@error_code(603)
class FileInArchiveNotFoundError(ArchiveError):
    "File not found in archive"
    def __init__(self, f, archive_f):
        return super().__init__("File ({}) not found in archive:{}".format(f, archive_f))

@error_code(604)
class UnsupportedArchiveError(ArchiveError):
    "Unsupported archive"
    def __init__(self, f):
        return super().__init__("Unsupported:{}".format(f))

    ## ETC.  -- CODE:900+ ##
@error_code(900)
class JSONParseError(ClientError, ServerError):
    """JSON parse error."""

    def __init__(self, json_data, name, msg):
        """init func."""
        pass
        # TODO: init both classs. log json_data.

