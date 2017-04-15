"""views module."""
import pprint

from flask import (render_template, g)
from happy_socketio import emit
from happypanda.webclient.main import happyweb, client, socketio
from happypanda.webclient.client import call_on_server, error_handler
from happypanda.common import constants, utils

log = utils.Logger(__name__)

@happyweb.before_first_request
def before_first_request():
    """before first request func."""
    client.connect()

@happyweb.before_request
def before_request():
    """before request func."""
    g.debug = constants.debug
    g.alive = client.alive
    g._params = utils.connection_params(web=True)

@happyweb.route('/')
@happyweb.route('/index')
def index():
    """index func."""
    data, error = call_on_server(client, "gallery_view", limit=100)
    if error:
        error_handler(error)
    galleries = []
    if "gallery_view" in data:
        galleries = data['gallery_view']['data']
    log.d("Showing", len(galleries), "galleries", galleries)
    return render_template('index.html',
                           galleries=galleries)

@happyweb.route('/gallery/page/<int:page>')
def gallery_page(page=0):
    data, error = call_on_server(client, "gallery_view", gallery_limit=100, page=page)
    if error:
        error_handler(error)
    return render_template('index.html', data)

@happyweb.route('/artist/page/<int:page>')
def artist_page(page=0):
    pass

@happyweb.route('/collection/page/<int:page>')
def collection_page(page=0):
    pass

@happyweb.route('/apiview')
def api_view(page=0):
    return render_template('api.html')

@socketio.on('connect')
def serv_connection():
    "Tests connection with server"
    status = client.alive()
    socketio.emit("connection", {"status": status})

@socketio.on('server_call')
def server_call(msg):
    fname = msg.pop('fname')
    if fname:
        data, error = call_on_server(client, fname, **msg)
        if error:
            error_handler(error)
        socketio.emit('server_call', {'data': data})
