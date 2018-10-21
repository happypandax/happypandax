Plugins
========================================

HPX is built in a way that makes it possible to step in and modify the way a functionality works or even add new ones with ease through plugins.

Plugins can be written in ``Python 3`` up to ``Python 3.6``.
Note that you don't need to be running HPX from source to develop a plugin.

Here you will learn how to create a HPX plugin and use it to extend HPX.
Before that though, here are some new terminologies to learn before diving in to help us better understand how everything is screwed together.

Terminology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Command**:

    Besides some core features that makes everything play nice together, a **command** is essentially what *a feature* in HPX is.
    An example of a command in HPX would be ``AddGallery``. This command, like its name implies, adds a gallery into HPX.
    **Commands** are self-contained and can act as a building-block for other commands (used by another command).
    Many of the functionalities provided by HPX are built up by using many different **commands**. These commands can range from being very simple doing just one small job
    to being complex and doing something big.

**Command entry**:

    This is what allows **commands** to be extensible. An **entry** allows other code to step in and run.
    In plugin terms, it's what allows a plugin handler to step in and run its code to either modify the process or do something else entirely.
    **Command entries** are defined by **commands** and it's up to a command when and how an **entry** is used.

**Command event**:

    A **command event** is almost like an **entry** with the difference that instead of modifying a process, a handler *reacts* to a process.
    Like an **entry**, it's up to a command when and to what an **event** is emitted.


Defining a plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we understand some basic concepts it's time to create a plugin.

HPX makes it very easy to create and write a plugin.

Plugins are contained in their own folder, so we start by creating one for our plugin::

    -/..
    -MyPlugin/

In this folder a manifest file named ``hplugin.json`` (case sensitive) is required::

    -/..
    -MyPlugin/
        - hplugin.json

A manifest file is a file describing a plugin. Inside ``hplugin.json`` is::

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

* ``id``: A UUID4 string. Unique across all plugins. This attribute is required to be present.
* ``entry``: Path to the entry python file. Path is relative to this folder and must exist. This attribute is required to be present.
* ``shortname``: Your plugin name in short form. Must be all lowercase and cannot exceed ``20`` characters nor contain any whitespace. This attribute is required to be present.
* ``name``: Name of your plugin. This attribute is required to be present.
* ``author``: Name of plugin author. This attribute is required to be present.
* ``version``: A string of the version of your plugin. Must conform :pep:`440`. This attribute is required to be present.

    Examples of versioning that conforms :pep:`440`::

        1.0.dev456, 1.0a1, 1.0a2.dev1, 1.0b1.dev4, 1.0rc1, 1.1.0b2, 1.1, 1.1.2

* ``description``: A description of your plugin. This attribute is required to be present.
* ``test``: Path to the entry file for tests. Path is relative to this folder and must exist. This attribute is optional.
* ``website``: A url to a website for the plugin, author, etc. This attribute is optional.
* ``require``: A list of strings defining other plugins as dependencies. This attribute is optional.

    A requirement must conform :pep:`508` with a few exceptions.

    Other plugins can be referred to by their id or shortname.

    Examples of requirements that conforms :pep:`508`::

        "otherplugin",
        "5c17829a-eca3-46fc-9d5e-da5804fdcbf5 == 3",
        "otherplugin <= 1.2",
        "5c17829a-eca3-46fc-9d5e-da5804fdcbf5 >= 3",
        "otherplugin >= 3.6,<2",
        "otherplugin >= 3; os_name=='posix'"

    Notice the marker ``os_name=='posix'`` in the last example. In addition to the default markers defined in :pep:`508`, HPX defines ``happypandax`` or ``hpx`` to check against the running HPX version.
    Markers can also be used freely like so::

        "happypandax >= 1.5.3", # indicates that this plugin requires this hpx version
        "platform_system == 'Windows'", # indicates that this plugin requires the windows platform
        "otherplugin < 2; platform_system=='Windows'", # indicates that otherplugin is only required on windows
        "otherplugin > 2; platform_system=='Linux'", # indicates that otherplugin is only required on linux
        "otherplugin == 2; happypandax==1.2" # indicates that otherplugin is only required on hpx version 1.2

After creating and defining a manifest file and create the entry files our final plugin folder looks like this::

    -/..
    -MyPlugin/
        - hplugin.json
        - main.py
        - test.py

And that's it! We can now have HPX load our plugin. To do that, place the plugin folder into one of the locations where HPX looks for plugins.
The default location is the ``plugins`` folder that exists inside the HPX root folder. It is also possible to define an additional location where to also look for plugins
through the setting ``plugin.plugin_dir``.

.. note::
    On a MacOS HPX installation, the root HPX folder is inside the bundle at ``HappyPanda X.app/Contents/MacOS/``.

After placing it in one of the locations, HPX should detect it and try to register it automatically either on startup or while running.
You can see if the plugin has been registered successfully if it appears on the plugin listing in a HPX client or if HPX doesn't print any warnings.

.. tip::

    It is recommended that you run HPX with the ``--debug`` and ``--dev`` commandline switches so that you can see what's going on when your plugin is being loaded and in use.
    See :ref:`Command-Line Arguments`.
    You can also disable all loggers except the plugin logger by adding them to the setting ``advanced.disabled_loggers`` to filter out all noise.

Writing a plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we've defined our plugin, we can now write the code for our plugin.

Please note that no code will be run *before* the plugin has been installed. A registered plugin is not the same as an installed plugin.
These are the different kind of states a plugin can be in: :class:`PluginState <happypanda.interface.enums.PluginState>`.

Interfacing with HPX
****************************************

HPX plugins run in a special environment with a special module named ``__hpx__`` to interface with HPX.

After a plugin has been registered, it can be installed. Installation has to be manually done by the user unless either of the two settings ``plugin.auto_install_plugin`` and ``plugin.auto_install_plugin_dependency``
are true.

When a plugin has been installed, it will be initialized. The entry file the plugin has provided in its manifest will be run upon initialization.
The entry file will be run in a special plugin environment and will be run just like any other Python code.

There are a couple of notable things about the plugin environment:

- The entry file's ``__name__`` will be set to ``__main__`` just like how Python does with its entry file.

.. note::

    The ``__file__`` attribute in the entry file is correctly set to be the path of the entry file.

- The plugin environment has been provided the special HPX interface module :mod:`__hpx__ <happypanda.core.plugin_interface>`.

- You can import any module and packages except ``happypanda``.

With all this in mind, we can now write code to interface with HPX. In the ``main.py``::

    import __hpx__ as hpx

    logger = hpx.get_logger(__name__)

    def main():
        logger.info("Emilia is best girl")
        logger.info(__file__)

    if __name__ == '__main__':
        main()

As you can see, we can write our code just like how we would write any regular Python program.
HPX gives this flexibility and freedom to its plugins.

The contents of the ``__hpx__`` module can be found at :ref:`Plugin API`, however, the most important methods from the module which we will cover here are
:meth:`attach <happypanda.core.plugin_interface.attach>` and :meth:`subscribe <happypanda.core.plugin_interface.subscribe>`.

The main point of a HPX plugin is to use these methods to extend what HPX is capable of.
Just like previously mentioned, HPX provides many **commands** that defines different entrypoints and events that we can use.

The method :meth:`subscribe <happypanda.core.plugin_interface.subscribe>` subscribes a handler function that we define to a command event.
HPX defines the plugin events ``init`` and ``disable`` that we can listen to.
We can use these events to initialize/terminate our stuff::

    import __hpx__ as hpx

    logger = hpx.get_logger(__name__)

    @hpx.subscribe("init")
    def init():
        log.info("Initialized")

    @hpx.subscribe("disable")
    def init():
        log.info("disabled")

    def main():
        logger.info("Emilia is best girl")
        logger.info(__file__)

    if __name__ == '__main__':
        main()

While it is true that we could also initialize on the module level, it is safer to do it on the ``init`` event reasons explained at :ref:`Commands`.

.. todo::
    
    commands and capture tokens

Logging and errors
****************************************

HPX provides a logging facility for its plugins.

When a plugin has been registered, a folder called ``logs`` is created in the plugin's folder. In this folder will reside ``plugin.log`` and ``plugin_debug.log``.

It is **strongly** recommended that you use this logging facility instead of rolling your own or using the ``logging`` module directly.
The HPX logging facility has been set up very intricately to make sense of the logs produced. 
Failing to use it will mess up how things are logged unless set up properly.
This can produce logs that are very confusing and useless to others.

``plugin.log`` is the normal log produced with a log level of ``INFO``.
``plugin_debug.log`` is a debug log produced only when the setting :ref:`debug <Settings>` has been set to true. The log level is ``DEBUG`` (basically captures everything).
The ``plugin_debug.log`` is also special in that its contents will be reset on every run.

These two files contain logs pertaining to the plugin in question.
HPX also has its own ``plugin.log`` found at ``[HPX]/logs/plugin.log`` that contain logs produced by all plugins (basically a combination of every plugin's exclusive log).

Debugging
****************************************

.. todo::
    
    debugging plugins

Testing
****************************************

.. todo::
    
    testing plugins

About thread safety
****************************************

.. todo::
    
    gevent and etc.

How to not break stuff
****************************************

While HPX provides plugins lots of freedom, this can sometimes lead to plugins being able to disrupt the flow of the program and/or create inexplicable bugs,
and generally make it so things are not working as intended.
Which is why care must be taken when writing plugins.

Here are some **DO**'s and **DON'T**'s that should ensure that everything plays nicely together.

* **DON'T** ever change the current working directory. Especially because of the issues explained in :ref:`thread safety <About thread safety>`.

* **DO** always prefer the :ref:`Plugin API` instead of rolling your own thing. If you think the API is limited and doesn't allow doing what you want to, consider opening a PR on Github instead.
* **DO** always prefer using the **commands** that HPX provides, especially because it allows other things that are beyond your control a chance to run.
* **DO** keep everything you produce in the plugin's own folder when possible. Use ``__hpx__.constants.current_dir`` to retrieve the path to the plugin's folder.

Importing modules and packages
****************************************

Importing modules works as expected and, other than ``happypanda``, all available modules can be imported normally::

    import modulename
    # .. code

It is also possible to import modules that you create yourself. Just put the file/folder in your plugin directory alongside your entry file and import it normally.

See :ref:`Available packages` for a list of all available modules in an HPX installation.

Importing external packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need an external package that is not listed in :ref:`Available packages` then here's what you can do.

.. todo::

    external packages


Available packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Aside from the python standard library, these are the available packages HPX provides that can be imported in the plugin environment.

.. exec::

    import sys
    import subprocess
    s = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'],
            encoding="utf-8")
    for x in s.split(): 
        print('*'+x+'*')
