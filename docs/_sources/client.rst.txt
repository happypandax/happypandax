Creating frontends
=============================================

HPX exposes an RPC interface over TCP making it possible to create a client in any programming language.

For exchanging data between the server and client ``JSON`` is used. Make sure you're familiar with ``JSON`` and its datatypes.

Before wanting to talk to a HPX server, make sure you have one running. Note that there's no need to run HPX from source if you just want to create a client.

It is recommended that you run the server with the ``--debug`` and ``--dev`` commandline switches so that you can see what's going on while you're connected.
See :ref:`Command-Line Arguments`.

Exchanging messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Needless to say, to start exchanging messages with the server, you need a basic understanding of TCP.

To communicate with the server you need to instantiate a TCP socket.

In your chosen programming language instantiate a TCP socket and connect it to the server.

In pseudocode::

    var sock = tcpsocket();
    sock.connect(server_address, server_port);

The server will try to talk to you after connecting successfully.

You receive this message.

In pseudocode::

    var msg = sock.receive();

**Now, the most important thing you need to understand is that the data you received just now might just be a part of the full message**.

The message is delimited so you keep receving data until you meet the EOF sequence. For HPX this EOF is ``<EOF>`` (in byte-form).

HPX requires that all data, **not including the EOF sequence**, to be gzipped.

A very crude example on how to receive a message from HPX in pseudocode:

::

    var msg = none
    var buffer = bytes("")

    while true:
        buffer += sock.receive() # might want to set a timeout so it doesn't wait forever
        
        # loop through buffer and check for EOF tag
        if bytes("<EOF>") in buffer:
            msg = buffer
            break # break loop
    # remove the EOF sequence from the data
    buffer = buffer.remove("<EOF>")
    # decompress the data
    var data = gzip.decompress(buffer)

Now that we got a message from the server, we convert it into valid ``JSON``.
The decompressed data is `UTF-8` encoded.

In pseudocode::

    var json_data = json.convert(data, encoding="utf-8");

And that's the end of it. You've successfully received a message from the server.

Sending a message is even easier. Just make sure it's valid ``JSON``, converted to bytes encoded in ``UTF-8`` and lastly gzip compressed before you send.

**Remember to suffix the message with the EOF tag so the server knows when your message is complete**.     

In pseudocode::

    var msg_to_send = bytes(valid_json, encoding="utf-8") # make sure it's UTF-8 encoded
    var eof_tag = bytes("<EOF>", encoding="utf-8")

    # compress the msg before sending
    msg_to_send = gzip.compress(msg_to_send)

    sock.send_everything(msg_to_send)
    sock.send_everything(eof_tag) # remember not to compress the EOF sequence!

For every message you send the server, a response is sent back, that is, unless the server has crashed or something.

(**Please note that if you ran the server with the --dev switch, the server will not respond to messages if an unhandled exception was raised**)

The structure of the messages exchanged between the server and the client is consistent::

    {
        "session": "",
        "name": "",
        "data": {},
    }

In ``name`` is a string value. This value is just an arbitrarily chosen name for the sever/client. It has some use, see :ref:`Configuration` when you're done reading this.

In ``data`` is the real message. ``session`` will be explained in :ref:`Session`.

**Every message should look like this**.

For the sake of brevity, from now on only messages meant to be put in the ``data`` key will be shown.

Generally, the server is very helpful and will tell you if your message is invalid and/or if you've misused or missed some keys.

Authenticating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Remember that the server always sent a message after you've successfully connected?

This is part of the authentication process or a so-called "handshake".

The server will send you a message that looks like this::

    {
        "version":
            {
                "core": [0, 0, 0] ", # [major, minor, patch]
                "db": [0, 0, 0],
                "torrent": [0, 0, 0]
            }
        "guest_allowed": true
    }

You can use this message to determine if the HPX server is supported or not.

Notice the ``guest_allowed`` key. The value of this key informs if it's possible to connect to the server *without* providing any credentials.

The server expects a response from the client that completes the handshake before any further processing is done.

To authenticate as a **guest** the client responds with an empty object ``{}``.

To authenticate as a **user** the client responds with::

    {
        "user": "",
        "password": ""
    }

The server will respond with ``"Authenticated"`` and assign a ``session`` for a successful handshake (this is the whole message)::

    {
        "session": "long_random_string",
        "name": "",
        "data": "Authenticated",
    }

If otherwise, it responds with an error. See ... for possible errors.

This handshake is only required *once* per initial connection.
Additional connections can be established without doing a handshake with the use of the newly-assigned ``session`` value.
See :ref:`Session`.

Additional connections 

.. todo::

    authentication errors

Session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After a successful handshake, a *session* is created::

    {
        "session": "a_new_unique_session_string",
        "name": "server",
        "data": "Authenticated",
    }

The session is tied to the context of the client who did the handshake.

The session is *not* tied to any particular connection, meaning multiple independent connections
can use the same session.

This allows for multiple independent connections to be made within the same or different app while sharing the same context::

    socketA (connects) --> server
    socketA <-- (asking for handshake) server
    socketA (handshakes) --> server
    socketA <-- (accepted, have a sessionid) server

    socketB (connects) --> server
    socketB <-- (asking for handshake) server
    socketB (normal msg with session id) --> server
    socketB <-- (normal response) server

Think of it as threads in a computer program.

As shown above, the server will *always* send a message when a client connects.
This message should thus always be consumed when connecting with additional sockets before sending the intended message with a session.

**Sessions have a limited lifespan**. Whenever you send a message using a session, you extend that particular session's lifespan.

Sessions expire when their lifespan runs out (shocking, isn't it? :) ), requiring the client to do a *new* handshake.

The extent of a single session's lifespan is set by the server (in the server settings).

.. todo::
    explain session expired error

Calling a function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that you've perfomed a successful handshake, you can start using the :ref:`Server API`.

A *function-call* object in its simplest looks like this::

    {
        "fname": ""
    }

The ``fname`` value is the name of the function you want to call. This particular object has no function arguments.

To add additional function arguments you just define the arguments in the *function-call* object like this::

    {
        "fname": "func1",
        "arg1": value1,
        "arg2": value2
    }

This *function-call* object will call ``func1(arg1=value1, arg2=value2)`` on the server.

It is possible to call multiple functions in a single message, which is why it is required that
*function-call* objects are put in a list before sending the message::

    [
        {
            "fname": "func1"
        },
        {
            "fname": "func2"
        }
    ]

The server will respond with a list of *function-data* objects::

    [
        {
            "fname": "func1",
            "data": {}
        },
        {
            "fname": "func2",
            "data": {}
        }
    ]

In case of errors raised by the function, the *function-data* gains an ``error`` key. See :ref:`Errors`.

If you're unsure on what data a function will return, see :ref:`Playing with the API`

.. todo::
    reference message objects here

Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An *error* object looks like this::

    {
        "code": integer,
        "msg": ""
    }

``code`` is the error code. See ... for available errors and error codes.

Errors occuring will be put in an ``error`` key.

Server-level errors (unhandled exceptions or errors not occuring in api-functions) will add
the ``error`` key at the root level of the payload::

    {
        "session": "",
        "name": "",
        "data": {},
        "error": {}
    }

Likewise, errors occuring in api-functions will add the ``error`` key in the *function-data* object::

    {
        "fname": "func2",
        "data": {},
        "error": {}
    }

Server commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The server implements server commands to control the server remotely: :class:`.ServerCommand`

Server commands are invoked like this (this is the whole payload)::

    {
        "session": "",
        "name": "",
        "data": server_command
    }

For example, if we want to shut down the server we use the :attr:`.ServerCommand.ServerQuit` command::

    {
        "session": "",
        "name": "clientname",
        "data": "serverquit"
    }

Some server commands will be broadcasted to all connected clients before executing.

For example, when the server recieves a shut down command, the exact command will be propogated and broadcasted to all connected clients::

    {
        "session": "",
        "name": "servername",
        "data": "serverquit"
    }

.. todo::
    
    server commands broadcasting (shutting down gracefully)

Playing with the API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default webclient has a place for watching and testing the exchanges between the server and the client.

Start the webclient with the ``--debug`` switch and go to ``/api``.

