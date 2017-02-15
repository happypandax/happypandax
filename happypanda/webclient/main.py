from flask import Flask

from happypanda.common import utils
from happypanda.clients.web.happy_socketio import SocketIO

happyweb = Flask(__name__, static_url_path='/static')
socketio = SocketIO(happyweb)
client = utils.Client("webclient")

from happypanda.clients.web import views # noqa: E402,F401