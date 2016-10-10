
import logging

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class HappypandaError(Exception):
    "Base Happypanda exception, all exceptions will derive from this"
    
    def __init__(self, msg):
        super().__init__()
        log_e(msg)

## CORE ##

class CoreError(HappypandaError):
    """Base Happypanda core exception, all core exceptions will derive from this

    Params:
        where -- where the error occured
        message -- explanation of error
    """
    
    def __init__(self, where, message):
        super().__init__(message)
        self.where = where
        self.msg = message


    ## PLUGINS ##

class PluginError(CoreError):
    """Base plugin exception, all plugin exceptions will derive from this

    Params:
        name -- name of plugin
        message -- explanation of error
    """
    
    def __init__(self, name, message):
        super().__init__("Plugin: " + name, message)

class PluginIDError(PluginError):
    ""
    pass

class PluginNameError(PluginIDError):
    ""
    pass

class PluginMethodError(PluginError):
    ""
    pass

class PluginAttributeError(PluginError):
    ""
    pass

class PluginHookError(PluginError):
    ""
    pass

class PluginHandlerError(PluginError):
    ""
    pass


    ## DATABASE ##

class DatabaseError(CoreError):
    """Base database exception, all database exceptions will derive from this"""
    pass

class DatabaseInitError(CoreError):
    ""
    def __init__(self, msg):
        super().__init__("An error occured in the database initialization process: " + msg)