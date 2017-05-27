from flask import Flask

from happypanda.common import utils, constants
from happypanda.webclient.client import Client
from happy_socketio import SocketIO

log = utils.Logger(__name__)

happyweb = Flask(__name__, static_url_path='/static')
socketio = SocketIO(happyweb)
client = Client("webclient")

# necessary to import AFTER
from happypanda.webclient import views  # noqa: E402,F401


def run(blocking=True):
    try:
        log.i(
            "Webserver successfully starting... ({}:{}) {}".format(
                constants.host_web,
                constants.port_webserver,
                "(blocking)" if blocking else ""),
            stdout=True)
        # OBS: will trigger a harmless socket.error when debug=True (stuff
        # still works)
        socketio.run(
            happyweb,
            *
            utils.connection_params(
                web=True),
            block=blocking,
            debug=constants.dev)
    except OSError as e:
        # include e in stderr?
        log.exception(
            "Error: Failed to start webserver (Port might already be in use)")


if __name__ == '__main__':
    run()
