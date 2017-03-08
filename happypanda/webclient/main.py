from flask import Flask

from happypanda.common import utils
from happypanda.webclient.client import Client
from happy_socketio import SocketIO

happyweb = Flask(__name__, static_url_path='/static')
socketio = SocketIO(happyweb)
client = Client("webclient")

# necessary to import AFTER
from happypanda.webclient import views # noqa: E402,F401

