from flask import (render_template, abort)
from happypanda.core.server import WebServer
from happypanda.core.client import Client
from happypanda.common import exceptions, hlogger

happyweb = WebServer.happyweb
socketio = WebServer.socketio

log = hlogger.Logger(__name__)

client = Client("webclient")
thumbclient = Client("webclient-thumbnails")
commandclient = Client("webclient-commands")

def send_error(ex):
    socketio.emit("exception", {'error': str(ex.__class__.__name__) + ': ' + str(ex)})

def sync_clients():
    for c in (thumbclient, commandclient):
        if not client.session == c.session:
            c.session = client.session

        if not c.alive():
            c.connect()

def call_server(msg, c):
    msg_id = msg['id']
    data = None
    try:
        serv_data = msg['msg']
        if not serv_data['session']:
            serv_data['session'] = client.session
        data = c.communicate(serv_data)
    except exceptions.ServerError as e:
        log.exception()
        send_error(e)

    return msg_id, data

@socketio.on('connect')
def on_connect():
    "client connected"
    pass


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
            if not client.alive():
                client.connect()
            d['status'] = client.alive()
        elif cmd == 2:
            if not client.alive():
                try:
                    client.connect()
                except exceptions.ClientError as e:
                    log.exception("Failed to reconnect")
                    send_error(e)
                d['status'] = client.alive()
        elif cmd == 3:
            if client.alive():
                client.close()
            d['status'] = client.alive()
        elif cmd == 4:
            d['status'] = client.alive()
        elif cmd == 5:
            client.request_auth()
            d['status'] = client._accepted
    except exceptions.ServerError as e:
        log.exception()
        send_error(e)
    socketio.emit("command", d)


@socketio.on('server_call')
def on_server_call(msg):
    msg_id, data = call_server(msg, client)
    socketio.emit('server_call', {'id': msg_id, 'msg': data})

@socketio.on('server_call', namespace='/thumb')
def on_thumb_call(msg):
    sync_clients()
    msg_id, data = call_server(msg, thumbclient)
    socketio.emit('server_call', {'id': msg_id, 'msg': data}, namespace='/thumb')

@socketio.on('server_call', namespace='/command')
def on_command_call(msg):
    sync_clients()
    msg_id, data = call_server(msg, commandclient)
    socketio.emit('server_call', {'id': msg_id, 'msg': data}, namespace='/command')

@happyweb.before_first_request
def before_first_request():
    """before first request func."""
    try:
        client.connect()
    except exceptions.ServerError as e:
        log.exception("Could not establish connection on first try")
        send_error(e)

@happyweb.route('/')
@happyweb.route('/index')
@happyweb.route('/library')
def library():
    return render_template('library.html')


@happyweb.route('/inbox')
def inbox(id=0):
    return render_template('library.html')


@happyweb.route('/fav')
def fav(id=0):
    return render_template('library.html')


@happyweb.route('/<item>/<int:id>')
def item_page(item='gallery', id=0):

    html_f = {'gallery': 'gallery.html', 'collection': 'collection.html'}

    h = html_f.get(item.lower())
    if not h:
        abort(404)
    return render_template(h)


@happyweb.route('/artist/<int:id>')
def artist_page(id=0):
    pass


@happyweb.route('/api')
def api_view(page=0):
    return render_template('api.html')

@happyweb.route('/thumb')
def thumbs_view(page=0):
    return render_template('api.html')