Plugins
========================================

HPX is built in a way that makes it possible to step in and modify the way a functionality works or even add new ones with ease with plug-ins.

Plug-ins are written in ``Python 3.6``.
Note that you don't need to be running HPX from source to develop a plug-in.

Here you will learn how to create a HPX plug-in and use it to extend HPX.
Before that though, here are some new terminologies to learn before diving in to help us better understand how everything is screwed together.

Terminology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Command**:

    Besides some core features that makes everything play nice together, a **command** is essentially what *a feature* in HPX is.
    An example of a command in HPX would be ``AddGallery``. This command, like its name implies, adds a gallery into HPX.
    **Commands** can act as a building-block for other commands (used by another command) or run by itself.
    Many of the functionalities provided by HPX are built up by many different **commands**. These commands can range from being very simple and do just one small job
    to being complex and doing something big.

**Command entry**:

    This is what allows **commands** to be extensible. An **entry** allows other code to step in and run.
    In plug-in terms, it's what allows a plug-in handler to step in and run its code to either modify the process or do something else entirely.
    **Command entries** are defined by **commands** and it's up to a command when and how an **entry** is used.

**Command event**:

    A **command event** is almost like an **entry** with the difference that instead of modifying a process, a handler *reacts* to a process.
    Like an **entry**, it's up to a command when and to what an **event** is emitted.


Defining a plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we understand some basic concepts it's time to create a plug-in.

HPX makes it very easy to create and write a plug-in.

Plug-ins are contained in their own folder, so we start by creating one for our plug-in::

    -/..
    -MyPlugin/

In this folder a manifest file named ``hplugin.json`` (case sensitive) is required::

    -/..
    -MyPlugin/
        - hplugin.json

A manifest file is a file describing a plug-in. Inside ``hplugin.json`` is::

    {
        "id": "5c17829a-eca3-46fc-9d5e-da5804fdcbf5",
        "entry": "main.py",
        "shortname": "myplugin",
        "name": "My Plugin",
        "author": "Twiddly",
        "version": "1.0.2b",
        "description": "A hpx plugin",
        "test": "test.py",
        "website": "www.twiddly.moe",
        "require": [
            "happypandax >= 0.0.0"
        ]
    }

* ``id``: A UUID4 string. Unique across all plug-ins. This attribute is required to be present.
* ``entry``: Path to the entry python file. Path is relative to this folder and must exist. This attribute is required to be present.
* ``shortname``: Your plug-in name in short form. Must be all lowercase and cannot exceed ``20`` characters nor contain any whitespace. This attribute is required to be present.
* ``name``: Name of your plug-in. This attribute is required to be present.
* ``author``: Name of plug-in author. This attribute is required to be present.
* ``version``: A string of the version of your plug-in. Must conform :pep:`440`. This attribute is required to be present.

    Examples of versioning that conforms :pep:`440`::

        1.0.dev456, 1.0a1, 1.0a2.dev1, 1.0b1.dev4, 1.0rc1, 1.1.0b2, 1.1, 1.1.2

* ``description``: A description of your plug-in. This attribute is required to be present.
* ``test``: Path to the entry file for tests. Path is relative to this folder and must exist. This attribute is optional.
* ``website``: A url to a website for the plug-in, author, etc. This attribute is optional.
* ``require``: A list of strings defining other plug-ins as dependencies. This attribute is optional.

    A requirement must conform :pep:`508` with a few exceptions.

    Other plug-ins can be referred by their id or shortname.

    Examples of requirements that conforms :pep:`508`::

        "otherplugin",
        "5c17829a-eca3-46fc-9d5e-da5804fdcbf5 == 3",
        "otherplugin <= 1.2",
        "otherplugin >= 3",
        "otherplugin >= 3.6,<2",
        "otherplugin >= 3; os_name=='posix'"

    Notice the marker ``os_name=='posix'`` in the last example. In addition to the default markers defined in :pep:`508`, HPX defines ``happypandax`` or ``hpx`` to check against the running HPX version.
    Markers can also be used freely like so::

        "happypandax >= 1.5.3",
        "platform_system == 'Windows'",
        "otherplugin < 2; platform_system=='Windows'", # only required on windows
        "otherplugin > 2; platform_system=='Linux'", # only required on linux
        "otherplugin == 2; happypandax==1.2" # only required on hpx version 1.2

After creating and defining a manifest file our final plug-in folder looks like this::

    -/..
    -MyPlugin/
        - hplugin.json
        - main.py
        - test.py

And that's it! We can now have HPX load our plug-in. To do that, place the plug-in folder into one of the locations where HPX looks for plug-ins.
The default location is the ``plugins`` folder that exists inside the HPX root folder. It is also possible to define an additional location where to also look for plug-ins
through the setting ``plugin.plugin_dir``.

.. note::
    On a MacOS HPX installation, the root HPX folder is inside the bundle at ``HappyPanda X.app/Contents/MacOS/``.

After placing it in one of the locations, HPX should detect it and try to register it automatically either on startup or while running.
You can see if the plugin has been registered successfully if it appears on the plugin listing in a HPX client or if HPX doesn't print any warnings.

.. tip::

    It is recommended that you run HPX with the ``--debug`` and ``--dev`` commandline switches so that you can see what's going when creating and writing a plug-in.
    See :ref:`Command-Line Arguments`.

Writing a plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we've defined our plug-in, we can now write the code for our plug-in.

Please note that no code will be run *before* the plug-in has been installed. A registered plug-in is not the same as an installed plug-in.

Interfacing with HPX
****************************************

Logging
****************************************

Errors
****************************************

Debugging
****************************************

About thread safety
****************************************

Available packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
