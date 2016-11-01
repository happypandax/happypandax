from flask import render_template, flash, request, url_for, redirect, abort, g
from happypanda.clients.web import happyweb

@happyweb.before_request
def beforeRequest():
    pass
    

@happyweb.route('/')
@happyweb.route('/index')
def index():
    return render_template('index.html')


