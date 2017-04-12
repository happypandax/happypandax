"""views module."""
from flask import (render_template, g)
from happy_socketio import emit
from happypanda.webclient.main import happyweb, client, socketio
from happypanda.webclient.client import call_on_server
from happypanda.common import constants, utils


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
    print(call_on_server(client, "gallery_view", gallery_limit=50))
    return render_template('index.html')

@happyweb.route('/gallery/page/<int:page>')
def gallery_page(page=0):
    pass

@happyweb.route('/artist/page/<int:page>')
def artist_page(page=0):
    pass

@happyweb.route('/collection/page/<int:page>')
def collection_page(page=0):
    pass

@socketio.on('connect')
def serv_connection():
    "Tests connection with server"
    status = client.alive()
    socketio.emit("connection", {"status": status})
    
    

