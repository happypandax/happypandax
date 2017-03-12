Plugins
========================================

It is possible to extend Happypanda X Server with plugins.
Understanding the plugin interface is relatively **easy** once you get the hang of it.

It is assumed that you are already familiar with the HPX developer environment: :ref:`Setting up an environment`

Things to know
----------------------------------------

- Plugins are written in ``Python 3``
- All plugins are placed in their own folder under the folder named ``plugins``

.. todo::
	specify python version

How to create a plugin
----------------------------------------

1. Start by creating a folder for your plugin, call it whatever describes your plugin and place it under the ``plugins`` folder in Happypanda X Server.

2. Create your main python file, which should end with the name ``HPlugin.py`` (case insensitive).

.. hint::
	| For example: ``MyPluginHPlugin.py``.
	| Your plugin can consist of multiple files but only one will be loaded, that is, your main file which is the file suffixed with ``HPlugin``.


That was the easy part. Now to the code.
The following are required by your main plugin file:

- A main plugin class that defines the following class attributes:
	- ``ID``: a unique UUID4 string, this is what others will use to interact with your plugin
	- ``NAME``: name of your plugin
	- ``AUTHOR``: Name of author
	- ``DESCRPTION``: A short description of your plugin
	- ``VERSION``: a tuple of 3 ints
	- ``WEBSITE``: This one is optional. Maybe your website, email or any way to contact you.

.. todo::
	``__init__`` able to take args


Putting all of this together we get the following:

My folder structure::

	plugins/MyPluginFolder
	- mainfilehplugin.py

In ``mainfilehplugin.py``::

	class MyPluginHPlugin:
		ID = "00000000-0000-0000-0000-000000000000"
		NAME = "MyPlugin"
		AUTHOR = "Pewpew"
		DESCRIPTION = "MyPlugin makes you a happy panda!"
		VERSION = (1, 0, 0)
		WEBSITE = "https://github.com/Pewpews/happypandax"

Interfacing with Happypanda X Server
----------------------------------------

.. todo::
	explain how to interface with hpx server

