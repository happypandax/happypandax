"""views module."""
from flask import (render_template, g)
from flask_socketio import emit
from happypanda.clients.web.main import happyweb, client, socketio


@happyweb.before_first_request
def before_first_request():
    """before first request func."""
    client._connect()

@happyweb.before_request
def before_request():
    """before request func."""
    g._versions = client._versions

@happyweb.route('/')
@happyweb.route('/index')
def index():
    """index func."""
    return render_template('index.html')

@socketio.on('connect')
def test_connection():
    "Tests connection with server"
    status = "Connected" if client.alive() else "Disconnected"
    socketio.send(status)
    
