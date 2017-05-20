"""views module."""
import pprint

from flask import (render_template, g)
from happy_socketio import emit
from happypanda.webclient.main import happyweb, client, socketio
from happypanda.common import constants, utils

log = utils.Logger(__name__)

@happyweb.before_first_request
def before_first_request():
    """before first request func."""
    client.connect()

@happyweb.route('/')
@happyweb.route('/index')
@happyweb.route('/library')
def library():
    return render_template('library.html')

@happyweb.route('/gallery/page/<int:page>')
def gallery_page(page=0):
    return render_template('library.html')

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
    socketio.emit("connection", {"status": status, "debug":constants.debug})

@socketio.on('call')
def server_call(msg):
    socketio.emit('response', client.communicate(msg))
