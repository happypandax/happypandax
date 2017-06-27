Contributing
#######################################

There are numerous of ways to contribute to HPX.

- You can create a plugin for HPX, see how to here.
- You can create a frontend in your favorite language, see how to here.
- You can help with misc. things like *helping answering issues on Github*, *fixing my spelling mistakes*, etc. 

If you want to start contributing to the HPX core parts, you will need to set up the right
environment and follow some simple guidelines. I appreciate any help.

Prerequisites
**************************************

| To start helping with the core parts, you will obviously need to know how to program in Python 3.
| I don't think there is anything else required. Don't hesitate to ask me if you have any questions.
You can find me at the Gitter channel. I try to respond within a day.

Setting up an environment
**************************************


We need to set up a virtual environment for our python packages

1. Install `Python 3.5 <https://www.python.org/>`_

.. Warning::
    Python 3.5 is the only supported version

2. Install ``virtualenv`` from pypi with ``pip3 install virtualenv``
3. Clone the `HPX <https://github.com/happypandax/server/tree/dev>`_ repo if you didn't already

Create a virtual environment in the cloned HPX repo folder like this:

4. In the cloned/downloaded folder, run this command: ``virtualenv env``

Activate the virtual environment and start installing the required dependencies

.. Note::
    | To activate on windows run: ``env\Scripts\activate.bat``
    | To activate on posix run: ``. env/bin/activate``

5. Install the dependencies: ``pip3 install -r requirements-dev.txt``

.. Warning::
    Windows users: If you get ``error: command '..\cl.exe' failed with exit status 2``, download ``bitarray`` from `here <(http://www.lfd.uci.edu/%7Egohlke/pythonlibs/#bitarray)>`_

Running
**************************************

See available command arguments: ``python run.py --help``

Start the server or webclient: ``python run.py``


Code Style
**************************************

We should all *try* to follow the official style guide `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_.

Run ``python lint.py`` when you are ready to make a PR on Github. You're good to go as long as this script returns no errors.

.. Note::
    Remember that code style fixes should always be in a separate commit!

Additonally, you could create a git hook for the pre-push event that'll automatically run ``lint.py`` for you everytime you do a ``git push``.

Create a file named ``pre-push`` at ``[HPX location]/.git/hooks`` with these contents::

    #![HPX location]/env/scripts/python.exe
    import os
    import sys
    from subprocess import run


    if __name__ == '__main__':
        os.chdir("[HPX location]")
        sys.exit(run(["python", "lint.py"]).returncode)

.. Warning::
    | Remember to replace ``[HPX location]`` with where your HPX folder is located.
    | Also, on posix, remember to make the file an exceutable with ``chmod +x <path-to-file>``

Testing
**************************************

`pytest <https://docs.pytest.org/en/latest/>`_ is used for running our tests.

It is important that new additions and functionalities are tested against.

Create or modify the tests in the the ``tests/`` folder.

Run ``python run_tests.py`` to run the tests.

Server
**************************************


Codebase
=====================================

::

    - root/
        - docs/source <- everything documentation in here
        - bin/ <- contains executables, dlls, etc.
        - tests/ <- everything test-related in here
        - happypanda/ <- the actual source code
            - common/ <- a package for common code
            - core/ <- the heart (or brain?) of it all
            - interface/ <- API for clients


Webclient
**************************************

A few things that you need to know when working on the webclient are:

- the frontend is actually written in *Python 3* and then **transpiled** to JavaScript.
- you need to rebuild the actual js files with ``python build_js.py`` everytime you edit the ``.py`` files in the ``static/`` folder
- make sure to read the `Transcrypt documentation <http://transcrypt.org/docs/html/index.html>`_ thoroughly (just do it. you'll regret not doing it, so just do it.)

The webclient is a generic Flask setup. Knowlegde of Flask is not required but beneficial.

Codebase
=====================================

::

    - root/
        - tests/ <- everything test-related in here
        - happypanda/ <- the actual source code
            - common/ <- a package for common code
            - static/ <- the python files transpiled to JavaScript among other things
            - templates/ <- HTML files
