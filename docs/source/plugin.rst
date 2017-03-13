Plugins
========================================

It is possible to extend Happypanda X Server with plugins.
Understanding the plugin interface is relatively **easy** once you get the hang of it.

It is assumed that you are already familiar with the HPX developer environment: :ref:`Setting up an environment`

Things to know
----------------------------------------

- Plugins are written in ``Python 3``
- All plugins are placed in their own folder in the folder named ``plugins``

.. todo::
	specify python version

How to create a plugin
----------------------------------------

1. Start by creating a folder for your plugin, call it whatever describes your plugin and place it under the ``plugins`` folder in Happypanda X Server.

2. Create your main python file, which should be named ``HPlugin.py`` (case insensitive).

.. hint::
	| Your plugin can consist of multiple files but only one will be loaded, that is, your main file which is named ``HPlugin.py``.


That was the easy part. Now to the code.
The following are required by your main plugin file:

- A main plugin class named ``HPlugin`` (case sensitive) that defines the following class attributes:
	- ``ID``: a unique UUID4 string, this is what others will use to interact with your plugin
	- ``NAME``: name of your plugin
	- ``AUTHOR``: Name of author
	- ``DESCRPTION``: A short description of your plugin
	- ``VERSION``: a tuple of 3 ints
	- ``WEBSITE``: This one is optional. Maybe your website, email or any way to contact you.
- Additionaly, in your main plugin class, a ``__init__`` method with the following signature must be defined: ``__init__(*args, **kwargs)``

Putting all of this together we get the following:

My folder structure::

	plugins/MyPluginFolder
	- hplugin.py

In ``hplugin.py``::

	class HPlugin:
		ID = "00000000-0000-0000-0000-000000000000"
		NAME = "MyPlugin"
		AUTHOR = "Pewpew"
		DESCRIPTION = "MyPlugin makes you a happy panda!"
		VERSION = (1, 0, 0)
		WEBSITE = "https://github.com/Pewpews/happypandax"

		def __init__(*args, **kwargs):
			pass

Interfacing with Happypanda X Server
----------------------------------------

.. todo::
	explain how to interface with hpx server

