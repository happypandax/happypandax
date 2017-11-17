import os

from flask import (render_template, abort, request, send_from_directory)
from werkzeug.utils import secure_filename

from happypanda.core.server import WebServer
from happypanda.core.client import Client
from happypanda.common import exceptions, hlogger, constants

happyweb = WebServer.happyweb
socketio = WebServer.socketio

log = hlogger.Logger(__name__)

all_clients = {}


def _create_clients(id, session_id=""):
    all_clients[id] = {
        "client": Client("webclient", session_id, id),
        "thumbclient": Client("webclient", session_id, id),
        "commandclient": Client("webclient", session_id, id)
    }
    return all_clients[id]


def _connect_clients(clients):
    clients["client"].connect()
    for c in clients:
        clients[c].connect()
        clients[c]._alive = clients["client"]._alive
        clients[c].session = clients["client"].session
        clients[c]._accepted = clients["client"]._accepted


def get_clients(id, session_id=""):
    if id not in all_clients:
        _create_clients(id, session_id)
    clients = all_clients[id]

    for c in clients:
        clients[c].session = clients['client'].session
    return clients


def send_error(ex):
    socketio.emit("exception", {'error': str(ex.__class__.__name__) + ': ' + str(ex)})


def call_server(msg, c):
    root_client = get_clients(request.sid)['client']
    msg_id = msg['id']
    data = None
    if c.alive():
        try:
            serv_data = msg['msg']
            if not serv_data['session']:
                serv_data['session'] = root_client.session
            data = c.communicate(serv_data)
        except exceptions.ServerError as e:
            log.exception()
            send_error(e)
    else:
        log.d("Cannot send because server is not connected:\n\t {}".format(msg))

    return msg_id, data


#@socketio.on('connect')
# def on_connect():
#    "client connected"
#    try:
#        _connect_clients(get_clients(request.sid))
#    except exceptions.ClientError as e:
#        log.exception("Failed to connect")
#        send_error(e)


@socketio.on('command')
def on_command(msg):
    """
    1 - connect
    2 - reconnect
    3 - disconnect
    4 - status
    5 - handshake
    Returns:
        {'status' : bool or None}
    """
    d = {'status': None}
    cmd = msg.get('command')
    d['command'] = cmd
    clients = get_clients(request.sid)
    try:
        if cmd == 1:
            if not clients['client'].alive():
                _connect_clients(clients)
            d['status'] = clients['client'].alive()
        elif cmd == 2:
            if not clients['client'].alive():
                try:
                    _connect_clients(clients)
                except exceptions.ClientError as e:
                    log.exception("Failed to reconnect")
                    send_error(e)
                d['status'] = clients['client'].alive()
        elif cmd == 3:
            if clients['client'].alive():
                clients['client'].close()
            d['status'] = clients['client'].alive()
        elif cmd == 4:
            d['status'] = clients['client'].alive()
        elif cmd == 5:
            clients['client'].request_auth()
            d['status'] = clients['client']._accepted
    except exceptions.ServerError as e:
        log.exception()
        send_error(e)
    socketio.emit("command", d)


@socketio.on('server_call')
def on_server_call(msg):
    c = get_clients(request.sid)
    msg_id, data = call_server(msg, c['client'])
    socketio.emit('server_call', {'id': msg_id, 'msg': data})


@socketio.on('server_call', namespace='/thumb')
def on_thumb_call(msg):
    c = get_clients(request.sid)
    msg_id, data = call_server(msg, c['thumbclient'])
    socketio.emit('server_call', {'id': msg_id, 'msg': data}, namespace='/thumb')


@socketio.on('server_call', namespace='/command')
def on_command_call(msg):
    c = get_clients(request.sid)
    msg_id, data = call_server(msg, c['commandclient'])
    socketio.emit('server_call', {'id': msg_id, 'msg': data}, namespace='/command')


#@happyweb.before_first_request
# def before_first_request():
#    """before first request func."""
#    global root_client
#    if not root_client:
#        root_client = Client("webclient")
#    try:
#        root_client.connect()
#    except exceptions.ServerDisconnectError as e:
#        log.exception("Could not establish connection on first try")
#        send_error(e)


@happyweb.route(constants.thumbs_view + '/<path:filename>')
def thumbs_view(filename):
    s_filename = secure_filename(filename)
    d = os.path.abspath(constants.dir_thumbs)
    f = s_filename
    if s_filename.endswith(constants.link_ext):
        p = os.path.join(constants.dir_thumbs, s_filename)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fp:
                img_p = fp.read()
            d, f = os.path.split(img_p)
    return send_from_directory(d, f)


@happyweb.route('/server', methods=['POST'])
def server_proxy():

    if request.json:
        pass
    abort(404)

# Let other routes take precedence


@happyweb.route('/', defaults={'path': ''})
@happyweb.route('/<path:path>')
def app_base(path):
    return render_template('base.html', same_machine=request.remote_addr == "127.0.0.1")
