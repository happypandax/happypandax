"""views module."""
from flask import (
    render_template,
)
from happypanda.clients.web.main import happyweb, client


@happyweb.before_first_request
def before_first_request():
    """before first request func."""
    client._connect()

@happyweb.route('/')
@happyweb.route('/index')
def index():
    """index func."""
    return render_template('index.html')
