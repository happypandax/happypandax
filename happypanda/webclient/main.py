from flask import Flask

from happypanda.common import utils
from happypanda.webclient.happy_socketio import SocketIO

happyweb = Flask(__name__, static_url_path='/static')
socketio = SocketIO(happyweb)
client = utils.Client("webclient")

from happypanda.webclient import views # noqa: E402,F401