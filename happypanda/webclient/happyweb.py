"""happyweb module."""
from flask import Flask


app = Flask(__name__)

route = app.route
before_request = app.route
