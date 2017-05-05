Contributing
========================================

There are numerous of ways to contribute to Happypanda X (referred to as HPX from now on).
If you want to start contributing to the HPX core parts, you will need to set up the right
environment and follow some simple guidelines.

Prerequisites
----------------------------------------

- ``Python 3.5``
- ``pip3``

Setting up an environment
----------------------------------------

We need to set up a virtual environment for our python packages

- Install ``virtualenv`` from pypi (``pip3 install virtualenv``)
- Clone the `HPX <https://github.com/Pewpews/happypandax/tree/dev>`_ repo if you didn't already

Create a virtual environment in the cloned HPX repo folder:

- ``cd`` into cloned folder: ``cd path/to/folder``
- `virtualenv env`

Activate the virtual environment and start installing the required dependencies

.. Note::
	| On windows: ``env\Scripts\activate.bat``
	| On posix: ``. env/bin/activate``

- Install the dependencies: ``pip install -r requirements-dev.txt``
- Build the js files:
	| ``python build_js.py``
- Build the docs (optional):
	| ``python build_docs.py``

HPX Structure
----------------------------------------

Code Style
----------------------------------------

Testing
----------------------------------------
