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
2. install ``virtualenv`` (``pip3 install virtualenv``)
3. clone or download Happypanda X
4. setup a ``virtualenv`` in the cloned/downloaded folder by running: ``virtualenv env``
5. activate the virtual env by running: (Posix: ``. env/bin/activate``) (Windows: ``env\Scripts\activate.bat``)
6. install the dependencies by running: ``pip3 install -r requirements.txt``

.. Warning::
    Windows users: If you get ``error: command '..\cl.exe' failed with exit status 2``, download ``bitarray`` from `here <http://www.lfd.uci.edu/%7Egohlke/pythonlibs/#bitarray>`_

7. build the javascript files to use the webclient by running: ``python3 build_js.py``

