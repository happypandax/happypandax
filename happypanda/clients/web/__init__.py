from flask import Flask

import os

happyweb = Flask(__name__, static_url_path='/static')

from happypanda.clients.web import views
