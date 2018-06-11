Contributing
#######################################

There are numerous of ways to contribute to HPX.

- You can create a plugin for HPX, see how to :ref:`here <Plugins>`.
- You can create a frontend in your favorite language, see how to :ref:`here <Creating frontends>`.
- You can help with misc. things like *helping answering issues on Github*, *fixing spelling mistakes*, etc. 

If you want to start contributing to the HPX core parts, you will need to set up the right
environment and follow some simple guidelines. I appreciate any help.

Prerequisites
**************************************

| To start helping with the core parts, you will obviously need to know how to program in Python 3.
| I don't think there is anything else required. Don't hesitate to ask me if you have any questions.
You can find me in the Gitter channel.

Setting up an environment
**************************************


1. install ``Python 3.6``, ``pip`` and ``nodejs``/``npm`` (if want to work on the webclient) 

.. Note::
    Python 3.6 is the version that HPX is tested and being developed on. It should also work on 3.7 and up but no guarantees.

2. run: ``python3 bootstrap.py --dev install``

3. run: ``python3 bootstrap.py`` for more information

.. Warning::
    Windows users: If you get an error during the install process, download ``bitarray`` from `here <(http://www.lfd.uci.edu/%7Egohlke/pythonlibs/#bitarray)>`_

    Install like this: ``.\env\Scripts\pip3.exe install bitarray.whl``

Running
**************************************

See available command arguments: ``python3 bootstrap.py run --help``

Start the server and webclient in development and debug mode: ``python3 bootstrap.py run --dev --debug``

.. tip::
    When developing on HPX, it is recommended that you use a development database. To do that, supply the `--dev-db` flag.

Code Style
**************************************

We should all *try* to follow the official style guide :pep:`8`.

Run ``python3 bootstrap.py lint`` (supply the ``-f`` flag to fix most issues automatically) when you are ready to make a PR on Github. You're good to go as long as this script returns no errors.

.. Note::
    Remember that code style fixes should always be in a separate commit!

Additonally, you could create a git hook for the pre-push event that'll automatically run ``lint.py`` for you everytime you do a ``git push``.

Create two files named ``pre-push`` and ``pre-push.py`` at ``[HPX location]/.git/hooks`` with these contents:

``pre-push``::

    #!/bin/sh
    
    # REMEMBER TO UNCOMMENT YOUR PLATFORM

    # POSIX
    #"env/bin/python" ".git/hooks/pre-push.py"

    # WINDOWS
    #"env/scripts/python.exe" ".git/hooks/pre-push.py"

``pre-push.py``::

    #!/usr/bin/python3
    import sys
    from subprocess import run

    if __name__ == '__main__':
        sys.exit(run([sys.executable, "lint.py"]).returncode)



.. Note::
    | On posix remember to make the ``pre-push`` file an exceutable with ``chmod +x .git/hooks/pre-push``

Testing
**************************************

`pytest <https://docs.pytest.org/en/latest/>`_ is used for running our tests.

It is important that new additions and functionalities are tested against.

Create or modify the tests in the the ``tests/`` folder.

Run ``python3 run_tests.py`` to run the tests.


Codebase
**************************************

::

    - root/
        - docs/source <- everything documentation in here
        - bin/ <- contains executables, dlls, etc.
        - tests/ <- everything test-related in here
        - static/ <- assets
        - templates/ <- the python source code to be transpiled to JavaScript among other things
        - happypanda/ <- the main source code
            - common/ <- a package for common code and modules
            - core/ <- the heart (or brain?) of it all
                - commands/ <- commands
            - interface/ <- API for clients


Webclient
=====================================

A few things that you need to know when working on the webclient are:

- the frontend is actually written in *Python 3* and then **transpiled** to JavaScript.
- you need to rebuild the actual js files with ``python3 bootstrap.py build --client`` everytime you edit the ``.py`` files in the ``templates/`` folder
- make sure to read the `Transcrypt documentation <http://transcrypt.org/docs/html/index.html>`_ thoroughly (do it. you'll regret not doing it because there's many *gotcha's*, so just do it.)

The webserver is a generic Flask setup. Knowlegde of Flask is not required but beneficial.


Editing the documentation
#######################################

The documentation is written in reStructuredText and is generated with Sphinx.
See `reStructuredText Primer <http://www.sphinx-doc.org/en/stable/rest.html#>`_ for an introduction.

To edit the documentation, start by `forking <https://github.com/happypandax/happypandax/>`_ the **main** repo.

The relevant source files are resided at ``docs/source``. Everything else in the docs folder is generated by Sphinx and should be ignored.
Edit the ``.rst`` files and then when done and satisfied, build the docs with ``python3 bootstrap.py build --docs``.

Note that not everything written in the documentation can be found at ``docs/source``. Some is also written in their respective python file.
For example, most of the :ref:`Server API` is written in the python files at ``happypanda/interface``.
Where possible, prefer writing in the relevant python files over the files at ``docs/source``. This makes it easier to manage.

After you're done editing the documentation, you can commit the changes. Don't worry, everything in the ``docs/`` folder except ``docs/source`` will be ignored by git so you can commit without worry.

Now that you have committed your changes, you can create a PR on github and it'll be merged into the main repo!
The live documentation found on github is built automatically on deployment.
