
class HappypandaError(Exception):
    "Base Happypanda exception, all exceptions will derive from this"
    pass

## CORE ##

class CoreError(HappypandaError):
    """Base Happypanda core exception, all core exceptions will derive from this

    Params:
        where -- where the error occured
        message -- explanation of error
    """
    
    def __init__(self, where, message):
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