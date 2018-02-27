Using HappyPanda X
========================================


A default HPX installation consists of the following two components:

- **HappyPanda X Server**

    The backbone of everything. HPX and its associated client's and/or plugins won't function without this running.

- **HappyPanda X Webclient**

    The default frontend that comes with HPX. A web-based (JS) frontend for HPX, if you will.

    This component should also be running, even if you're not going to use the client.
    It should be started automatically on server start.

Setting up
-------------------------------------

A good idea before starting HPX is to go through the available settings that configure how HPX should be running.
You can see the available settings :ref:`here <Settings>`.

To use these settings, you create a file named ``config.yaml`` in the root directory of HPX.

You can create an example file with all settings listed if you run this command: ``./happypandax --gen-config`` or ``python3 run.py --gen-config`` if you're running from source.

.. note::
    On a MacOS HPX installation, the root HPX folder is inside the bundle at ``HappyPanda X.app/Contents/MacOS/``.

    On Windows the executable is named ``happypandax.exe`` (with ``.exe`` suffix).

Most of these settings can also be configured from a HPX client.

.. warning::
    Not all settings work or have been implemented yet. You should leave these settings untouched for now: ``server.disable_default_user``, ``server.require_auth``, ``server.expose_server`` and ``server.allow_guests``.


Starting
-------------------------------------

There are two ways of starting up HPX.

If you're running from source you start HPX either through ``run.py`` or ``gui.py``.

If from installation, there exists the two executables named ``happypandax`` and ``happypandax_gui``.

The `gui.py` or `happypandax_gui` is just a GUI wrapper around ``run.py`` or ``happypandax`` to provide a user-friendly way of starting HPX.

Before starting, you can see the available arguments by supplying the ``--help`` argument on the commandline/terminal: ``python3 ./run.py --help`` or ``./happypandax --help``.
You can also refer to :ref:`Command-Line Arguments`. 

To start the server (and the webclient) you just run: ``python3 ./run.py`` or doubleclick on the executable ``happypandax``.
You can also instead start the GUI wrapper, and it should be self-explanatory how to start the server from there.

.. note::
    On a MacOS HPX installation, the app bundle is set to run ``happypandax_gui``.


Migrating from HappyPanda
-------------------------------------

In the HPX root folder, you can find a commandline tool named ``HPtoHPX`` to help convert your HP database.
See available arguments by supplying the ``--help`` argument: ``./HPtoHPX --help``.

Convert your HP database like this: ``./HPtoHPX path/to/old/file.db data/happypanda.db``

Alternatively, you can also use the GUI wrapper ``happypandax_gui``, which provides an user-friendly way of doing it.

Using
-------------------------------------

If you started HPX, you can start using HPX right away by opening up your browser and going to 
``localhost:7008`` *(replace ``7008`` with whatever port you chose the webclient server to listen on)*

What else you could do is look for another client to use HPX with. They can come in all forms (mobile apps, pc software, etc.) as long as someone builds it.
If you're interested in building a client to work with HPX, head over to :ref:`Creating frontends` for an introduction.

Since a HPX client cannot function without the server running, it is a good idea to always leave the HPX server running in the background.


Exposing Happypanda X
========================================

To allow HPX to be accessed from your phone or other devices, you'll need to expose the server(s) to the private or public (internet) networks

.. todo::
    expose HPX

Private network
-------------------------------------

Doing this will allow for you to access HPX from *any device connected to your home network*

Public network
-------------------------------------

Doing this will allow for you to access HPX from *any device connected to the internet*

