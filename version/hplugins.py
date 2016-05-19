import logging
import os
import uuid
import threading
import sys

from PyQt5.QtCore import pyqtWrapperType

log = logging.getLogger(__name__)
log_i = lambda a: None
log_d = lambda a: None
log_w = lambda a: None
log_e = lambda a: None
log_c = lambda a: None

class PluginError(ValueError):
	pass

class PluginIDError(PluginError):
	pass

class PluginNameError(PluginIDError):
	pass

class PluginMethodError(PluginError):
	pass

class Plugins:
	""
	_connections = []
	_plugins = {}
	_pluginsbyids = {}
	hooks = {}


	def register(self, plugin):
		assert isinstance(plugin, HPluginMeta)
		self.hooks[plugin.ID] = {}
		self._plugins[plugin.NAME] = plugin() # TODO: name conflicts?
		self._pluginsbyids[plugin.ID] = self._plugins[plugin.NAME]

	def _connectHooks(self):
		for plugin_name, pluginid, h_name, handler in self._connections:
			log_i("{}:{} connection to {}:{}".format(plugin_name, handler, pluginid, h_name))
			print(self.hooks)
			try:
				p = self.hooks[pluginid]
			except KeyError:
				log_e("Could not find plugin with plugin id: {}".format(pluginid))
				return
			try:
				h = p[h_name]
			except KeyError:
				log_e("Could not find pluginhook with name: {}".format(h_name))
				return
		
			h.addHandler(handler, (plugin_name, pluginid))
		return True

	def __getattr__(self, key):
		try:
			return self._plugins[key]
		except KeyError:
			raise PluginNameError(key)

registered = Plugins()

class HPluginMeta(pyqtWrapperType):

	def __init__(cls, name, bases, dct):
		if not name.endswith("HPlugin"):
			log_e("Main plugin class should end with name HPlugin")
			return

		if not hasattr(cls, "ID"):
			log_e("ID attribute is missing")
			return
		cls.ID = cls.ID.replace('-', '')
		if not hasattr(cls, "NAME"):
			log_e("NAME attribute is missing")
			return
		if not hasattr(cls, "VERSION"):
			log_e("VERSION attribute is missing")
			return
		if not hasattr(cls, "AUTHOR"):
			log_e("AUTHOR attribute is missing")
			return
		if not hasattr(cls, "DESCRIPTION"):
			log_e("DESCRIPTION attribute is missing")
			return

		try:
			val = uuid.UUID(cls.ID, version=4)
			assert val.hex == cls.ID
		except ValueError:
			log_e("Invalid plugin id. UUID4 is required.")
			return
		except AssertionError:
			log_e("Invalid plugin id. A valid UUID4 is required.")
			return

		if not isinstance(cls.NAME, str):
			log_e("Plugin name should be a string")
			return
		if not isinstance(cls.VERSION, tuple):
			log_e("Plugin version should be a tuple with 3 integers")
			return
		if not isinstance(cls.AUTHOR, str):
			log_e("Plugin author should be a string")
			return
		if not isinstance(cls.DESCRIPTION, str):
			log_e("Plugin description should be a string")
			return

		super().__init__(name, bases, dct)

		setattr(cls, "connectPlugin", cls.connectPlugin)
		setattr(cls, "newHook", cls.createHook)
		setattr(cls, "connectHook", cls.connectHook)
		setattr(cls, "__getattr__", cls.__getattr__)

		registered.register(cls)

	def connectPlugin(cls, pluginid, plugin_name):
		"""
		Connect to other plugins
		Params:
			pluginid: PluginID of the plugin you want to connect to
			plugin_name: Name you want to referrer the other plugin as

		Other methods of other plugins can be used as such: self.plugin_name.method()
		"""

		class OtherHPlugin:

			def __init__(self, pluginid):
				self._id = pluginid.replace('-', '')
	
			def __getattr__(self, key):
				try:
					plugin = registered._pluginsbyids[self._id]
					
					pluginmethod = getattr(plugin, key, None)
					if pluginmethod:
						return pluginmethod 
					else:
						raise PluginMethodError(key)
				except KeyError:
					raise PluginIDError(self._id)

		setattr(cls, plugin_name, OtherHPlugin(pluginid))

	def connectHook(self, pluginid, hook_name, handler):
		"""
		Connect to other plugins' hooks
		Params:
			pluginid: PluginID of the plugin that has the hook you want to connect to
			hook_name: Exact name of the hook you want to connect to
			handler: Your custom method that should be executed when the other plugin uses its hook.
		"""

		assert isinstance(pluginid, str) and isinstance(hook_name, str) and callable(handler), ""
		registered._connections.append((self.NAME, pluginid.replace('-', ''), hook_name, handler))

	def createHook(self, hook_name):
		"""
		Create hooks that other plugins can extend
		Params:
			hook_name: Name of the hook you want to create.
		
		Hook will be used as such: self.hook_name()
		"""

		assert isinstance(hook_name, str), ""

		class Hook:
			_handlers = set()
			def addHandler(self, handler, pluginfo):
				self._handlers.add((handler, pluginfo))

			def __call__(self, *args, **kwargs):
				handler_returns = []
				for handlers, pluginfo in self._handlers:
					try:
						handler_returns.append(handlers(*args, **kwargs))
					except Exception as e:
						raise PluginError("{}:{}".format(pluginfo[0], pluginfo[1]))
				return handler_returns

		h = Hook()
		registered.hooks[self.ID][hook_name] = h

	def __getattr__(self, key):
		try:
			return registered.hooks[self.ID][key]
		except KeyError:
			return PluginMethodError(key)

#def startConnectionLoop():
#	def autoConnectHooks():
#		run = True
#		while run:
#			run = registered._connectHooks()
#	auto_t = threading.Thread(target=autoConnectHooks)
#	auto_t.start()