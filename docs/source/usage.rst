Using Happypanda X
========================================


Default HPX consists of the following components:

- Happypanda X Server
	.. hint::

		The backbone of everything. HPX won't function without this running.

- Happypanda X Web client
	.. hint::

		The default frontend that comes with HPX. A web-based (JS) frontend for HPX.

Starting up
-------------------------------------



From source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See available command arguments: ``python run.py --help``

Start the server: ``python run.py -s``

Start the web client server: ``python run.py -w``

From executable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Using
-------------------------------------

If you started the web client server, you can start using HPX by opening up your browser and going to 
``localhost:7008`` *(replace ``7008`` with whatever port you chose the web client server to listen on)*

Exposing Happypanda X
========================================

To allow HPX to be accessed from your phone or other devices, you'll need to expose the server(s) to the private or public (internet) networks

Private network
-------------------------------------

Doing this will allow for you to access HPX from *any device connected to your home network*

Public network
-------------------------------------

Doing this will allow for you to access HPX from *any device connected to the internet*

