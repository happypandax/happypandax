import os

from flask import (render_template, abort, request, send_from_directory)
from werkzeug.utils import secure_filename

from happypanda.core.server import WebServer
from happypanda.core.client import Client
from happypanda.common import exceptions, hlogger, constants

happyweb = WebServer.happyweb
socketio = WebServer.socketio

log = hlogger.Logger(__name__)

root_client = None

all_clients = {}


def _create_clients(id, session_id=""):
    all_clients[id] = {
        "client": Client("webclient", session_id, id),
        "thumbclient": Client("webclient-thumbnails", session_id, id),
        "commandclient": Client("webclient-commands", session_id, id)
    }
    return all_clients[id]


def get_clients(id, session_id=""):
    if id not in all_clients:
        _create_clients(id, session_id)
    clients = all_clients[id]

    if session_id:
        for c in clients.values():
            if not c.alive() or c.session != session_id:
                c.session = session_id
                c.connect()
    return clients


def send_error(ex):
    socketio.emit("exception", {'error': str(ex.__class__.__name__) + ': ' + str(ex)})


def call_server(msg, c):
    msg_id = msg['id']
    data = None
    try:
        serv_data = msg['msg']
        if not serv_data['session']:
            serv_data['session'] = root_client.session
        data = c.communicate(serv_data)
    except exceptions.ServerError as e:
        log.exception()
        send_error(e)

    return msg_id, data


@socketio.on('connect')
def on_connect():
    "client connected"
    global root_client
    if not root_client:
        root_client = Client("root_webclient")
    get_clients(request.sid, root_client.session)


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
    try:
        if cmd == 1:
            if not root_client.alive():
                root_client.connect()
            d['status'] = root_client.alive()
        elif cmd == 2:
            if not root_client.alive():
                try:
                    root_client.connect()
                except exceptions.ClientError as e:
                    log.exception("Failed to reconnect")
                    send_error(e)
                d['status'] = root_client.alive()
        elif cmd == 3:
            if root_client.alive():
                root_client.close()
            d['status'] = root_client.alive()
        elif cmd == 4:
            d['status'] = root_client.alive()
        elif cmd == 5:
            root_client.request_auth()
            d['status'] = root_client._accepted
    except exceptions.ServerError as e:
        log.exception()
        send_error(e)
    socketio.emit("command", d)


@socketio.on('server_call')
def on_server_call(msg):
    c = get_clients(request.sid, root_client.session)
    msg_id, data = call_server(msg, c['client'])
    socketio.emit('server_call', {'id': msg_id, 'msg': data})


@socketio.on('server_call', namespace='/thumb')
def on_thumb_call(msg):
    c = get_clients(request.sid, root_client.session)
    msg_id, data = call_server(msg, c['thumbclient'])
    socketio.emit('server_call', {'id': msg_id, 'msg': data}, namespace='/thumb')


@socketio.on('server_call', namespace='/command')
def on_command_call(msg):
    c = get_clients(request.sid, root_client.session)
    msg_id, data = call_server(msg, c['commandclient'])
    socketio.emit('server_call', {'id': msg_id, 'msg': data}, namespace='/command')


@happyweb.before_first_request
def before_first_request():
    """before first request func."""
    global root_client
    if not root_client:
        root_client = Client("root_webclient")
    try:
        root_client.connect()
    except exceptions.ServerError as e:
        log.exception("Could not establish connection on first try")
        send_error(e)


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
    return render_template('base.html')
