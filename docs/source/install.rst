Installing
#######################################

1. Download the archive/installer matching your OS from `Github Releases <https://github.com/happypandax/server/releases>`_
2. Extract the archive or run the installer
3. Continue to :ref:`Using HappyPanda X`

HPX is self-contained.
Everything HPX creates and modifies, it does so in its own folder.
This means it's portable.
The installer is just there to ease the install.
On Windows it creates 3 shortcuts to ``happypandax_gui.exe``.
They are placed in your ``Desktop``, ``Start Menu`` and ``Start Menu/Programs`` folders.

If you're on Windows < 10, you need to install ``Microsoft Visual C++ Redistributable 2015`` to run HPX.
The setup file is included in the archive, look for ``vc_redist.x86.exe``.
If you're using the installer, this setup file will automatically be run for you.

.. Warning::
    HPX requires sufficient permissions to read and write from it's own folder to be able to run properly. This is required for the auto-update process to work.
    On Windows it means you shouldn't install HPX somewhere like ``C:\Program Files (x86)``. If you still choose to do so just remember to run HPX as admin.
    (Not recommended)


If you wish to develop directly on HPX please head to :ref:`Setting up an environment`.