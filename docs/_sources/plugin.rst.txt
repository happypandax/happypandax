Plugins
========================================

It is possible to extend Happypanda X Server with plugins.

You should be already familiar with the HPX dev environment: :ref:`Setting up an environment` to begin working on HPX plugins.

Before creating a plugin
----------------------------------------

- Plugins are written in the same language as HPX server, namely ``Python 3.5``.
- Plugins are contained in their own folder inside the folder named ``plugins`` found at the root-level.

Developing a plugin
----------------------------------------

1. Start by creating a folder for your plugin, call it whatever describes your plugin and place it in the ``plugins`` folder at the root-level.

2. Create your main python file, which should be named ``HPlugin.py`` (case insensitive).

.. hint::
	| Your plugin can consist of multiple files but only one will be loaded, that is, your main file which is named ``HPlugin.py``.


The following is required by your main plugin file:

- A main plugin class named ``HPlugin`` (case sensitive) that defines the following class attributes:
	- ``ID``: a unique UUID4 string, this is what others will use to interact with your plugin
	- ``NAME``: name of your plugin
	- ``AUTHOR``: Name of author
	- ``DESCRPTION``: A short description of your plugin
	- ``VERSION``: a tuple of 3 ints
	- ``WEBSITE``: This one is optional. Maybe your website, email or any way to contact you.

- Additionally, in your main plugin class, a ``__init__`` method with the following signature must be defined: ``__init__(self, *args, **kwargs)``

.. todo::
	explain ``REQUIRE``

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

		def __init__(self, *args, **kwargs):
			pass

.. todo::
	consider creating a cookiecutter project template

Interfacing with HPX
----------------------------------------


Testing a plugin
----------------------------------------