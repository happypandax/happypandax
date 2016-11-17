from flask import Flask

import os

from happypanda.common import utils

happyweb = Flask(__name__, static_url_path='/static')
client = utils.Client("webclient")

from happypanda.clients.web import views


