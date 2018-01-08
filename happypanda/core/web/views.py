import os
import socket

from flask import (render_template, abort, request, send_from_directory)
from werkzeug.utils import secure_filename
from gevent.lock import BoundedSemaphore

from happypanda.core.client import Client
from happypanda.common import exceptions, hlogger, constants, utils

happyweb = None
socketio = None

log = hlogger.Logger(__name__)

all_clients = {}
all_locks = {}


def _create_clients(id, session_id=""):
    all_clients[id] = {
        "client": Client("webclient", session_id, id),
        "notification": Client("notification", session_id, id),
        "command": Client("command", session_id, id)
    }
    return all_clients[id]


def _create_locks(id):
    all_locks[id] = {
        "client": BoundedSemaphore(),
        "notification": BoundedSemaphore(),
        "command": BoundedSemaphore()
    }
    return all_locks[id]


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


def get_locks(id):
    if id not in all_locks:
        _create_locks(id)
    return all_locks[id]


def send_error(ex, **kwargs):
    socketio.emit("exception",
                  {'error': str(ex.__class__.__name__) + ': ' + str(ex)},
                  **kwargs
                  )


def call_server(msg, client, lock):
    msg_id = msg['id']
    data = None
    try:
        lock.acquire()
        root_client = get_clients(msg.get("session_id", "default"))['client']
        if client.alive():
            try:
                serv_data = msg['msg']
                if not serv_data['session']:
                    serv_data['session'] = root_client.session
                data = client.communicate(serv_data)
            except exceptions.ServerError as e:
                log.exception()
                send_error(e)
        else:
            log.d("Cannot send because server is not connected:\n\t {}".format(msg))
    finally:
        lock.release()

    return msg_id, data


def is_same_machine():
    # TODO: this will fail if connected to external server
    addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    addr = addr.split("%")[0]
    local_adresses = [
        "::1", "127.0.0.1",
        utils.get_local_ip()
        ]

    # IPV6
    # TODO: find a workaround for OSX
    if not constants.is_osx:
        local_adresses.append(socket.gethostbyaddr(socket.gethostbyname())[2][0])

    if addr in local_adresses:
        return True
    return False


def on_command_handle(client_id, clients, msg):
    d = {'status': None}
    cmd = msg.get('command')
    d['command'] = cmd
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
                    send_error(e, room=client_id)
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
        send_error(e, room=client_id)
    socketio.emit("command", d, room=client_id)


def on_server_call_handle(client_id, client, lock, msg, **kwargs):
    msg_id, data = call_server(msg, client, lock)
    socketio.emit('server_call', {'id': msg_id, 'msg': data}, room=client_id, **kwargs)


def init_views(flask_app, socketio_app):
    global happyweb
    global socketio

    happyweb = flask_app
    socketio = socketio_app

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
        clients = get_clients(msg.get("session_id", "default"))
        socketio_app.start_background_task(on_command_handle, request.sid, clients, msg)

    @socketio.on('server_call')
    def on_server_call(msg):
        clients = get_clients(msg.get("session_id", "default"))
        locks = get_locks(msg.get("session_id", "default"))
        socketio_app.start_background_task(
            on_server_call_handle,
            request.sid,
            clients['client'],
            locks['client'],
            msg)

    @socketio.on('server_call', namespace='/notification')
    def on_push_call(msg):
        clients = get_clients(msg.get("session_id", "default"))
        locks = get_locks(msg.get("session_id", "default"))
        socketio_app.start_background_task(
            on_server_call_handle,
            request.sid,
            clients['notification'],
            locks['notification'],
            msg, namespace='/notification')

    @socketio.on('server_call', namespace='/command')
    def on_command_call(msg):
        clients = get_clients(msg.get("session_id", "default"))
        locks = get_locks(msg.get("session_id", "default"))
        socketio_app.start_background_task(
            on_server_call_handle,
            request.sid,
            clients['command'],
            locks['command'],
            msg, namespace='/command')

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
        return render_template('base.html',
                               dev=constants.dev,
                               same_machine=is_same_machine(),
                               version=".".join(str(x) for x in constants.version_web))
