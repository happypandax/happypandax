Installing
#######################################

Windows
**************************************
Refer to building.

Linux
**************************************
Refer to building.

Mac OSX
**************************************
Refer to building.

Building
#######################################

1. install ``Python 3.5`` and ``pip``

.. Note::
    Python 3.5 is currently the only supported version

2. install ``virtualenv`` (``pip3 install virtualenv``)
3. clone or download Happypanda X from the github repository
4. setup a ``virtualenv`` in the cloned/downloaded folder by running: ``virtualenv env``
5. activate the virtual env by running: (Posix: ``. env/bin/activate``) (Windows: ``env\Scripts\activate.bat``)
6. install the dependencies by running: ``pip3 install -r requirements.txt``

.. Warning::
    Windows users: If you get ``error: command '..\cl.exe' failed with exit status 2``, download ``bitarray`` from `here <http://www.lfd.uci.edu/%7Egohlke/pythonlibs/#bitarray>`_

7. to build and use the default frontend, run: ``python3 build_webclient.py``

