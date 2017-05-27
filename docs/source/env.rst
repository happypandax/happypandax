========================================
Contributing
========================================

There are numerous of ways to contribute to HPX.

- You can create a plugin for HPX, see how to here.
- You can create a frontend in your favorite language, see how to here.
- You can help with misc. things like *helping answering issues on Github*, *fixing my spelling mistakes*, etc. 

If you want to start contributing to the HPX core parts, you will need to set up the right
environment and follow some simple guidelines. I appreciate any help.

Prerequisites
----------------------------------------

| To start helping with the core parts, you will obviously need to know how to program in Python 3.
| I don't think there is anything else required. Don't hesitate to ask me if you have any questions.
You can find me at the Gitter channel. I try to respond within a day.

Setting up an environment
----------------------------------------

We need to set up a virtual environment for our python packages

1. Install `Python 3.5 <https://www.python.org/>`_ and pip
2. Install ``virtualenv`` from pypi with ``pip3 install virtualenv``
3. Clone the `HPX <https://github.com/Pewpews/happypandax/tree/dev>`_ repo if you didn't already

Create a virtual environment in the cloned HPX repo folder like this:

4. In the cloned/downloaded folder, run this command: ``virtualenv env``

Activate the virtual environment and start installing the required dependencies

.. Note::
	| To activate on windows run: ``env\Scripts\activate.bat``
	| To activate on posix run: ``. env/bin/activate``


5. Install the dependencies: ``pip3 install -r requirements-dev.txt``

To use the web client, you need to first build the javascript files:

6. Build the js files: ``python build_js.py``

And lastly, to build this documentation for offline view:

7. Build the docs ``python build_docs.py``

Running
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See available command arguments: ``python run.py --help``

Start the server: ``python run.py -s``

Start the web client server: ``python run.py -w``


Internal Structure
----------------------------------------

::

	- root/
		- docs/ <- everything documentation in here
		- bin/ <- contains executables, dlls, etc.
		- tests/ <- everything test-related in here
		- happypanda/ <- the actual source code
			- common/ <- a package for common code to be included by both server and webclient
			- server/ <- the HPX server
				- core/ <- the heart (or brain?) of it all
				- interface/ <- API for clients
			- webclient/ <- the HPX web client frontend (contains a generic Flask setup)
				- static/ <- in here contains the actual visual frontend code


Working on the web client
----------------------------------------

A few things that you need to know when working on the web client are:

- the frontend is actually written in *Python 3* and then **transpiled** to JavaScript.
- you need to rebuild the actual js files with ``python build_js.py`` everytime you edit the ``.py`` files in the ``static/`` folder
- make sure to read the `Transcrypt documentation <http://transcrypt.org/docs/html/index.html>`_ thoroughly (just do it. you'll regret not doing it, so just do it.)

Code Style
----------------------------------------

We should all *try* to follow the official style guide `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_.

Run ``python lint.py`` when you are ready to make a PR on Github. You're good to go as long as this script returns no errors.

.. Note::
	Remember that code style fixes should always be in a separate commit!

Testing
----------------------------------------

It is important that new additions or functionalities are tested against.

Create or modify the tests in the the ``tests/`` folder.

Run ``python run_tests.py`` to run the tests.
