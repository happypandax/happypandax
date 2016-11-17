"""views module."""
from flask import (
    render_template,
)
from happypanda.clients.web import happyweb


@happyweb.before_request
def before_request():
    """before request func."""
    pass


@happyweb.route('/')
@happyweb.route('/index')
def index():
    """index func."""
    return render_template('index.html')
