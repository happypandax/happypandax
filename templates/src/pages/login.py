from src.react_utils import (e, h,
                             createReactClass)
from src.ui import ui
from src.state import state
from src.i18n import tr
from src.client import client
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

def submit():
    uinfo = {}
    if this.state.user:
        uinfo['username'] = this.state.user
    if this.state['pass']:
        uinfo['password'] = this.state['pass']
    this.connect(uinfo)

def connect(uinfo):
    if client._connection_status:
        client.send_command(client.commands['handshake'], uinfo, this.on_handshake)
        this.setState({'loading':True})

def on_handshake(msg):
    this.setState({'loading':False})
    if this.props.on_login:
        this.props.on_login(msg['accepted'])

def page_render():
    els = []
    if state['guest_allowed']:
        els.append(e(ui.Button, tr(this, "ui.t-continue-as-guest", "Connect as guest"),
                     fluid=True, primary=True, onClick=this.as_guest))
        els.append(e(ui.Divider, tr(this, "ui.t-or", "Or"), horizontal=True))

    return e(ui.Segment,
             this.props.children,
             *els,
             e(ui.Form,
                e(ui.Form.Input,
                label=tr(this, "ui.t-username", "Username"),
                placeholder="default",
                width=10,
                onChange=this.set_user,
                ),
                e(ui.Form.Input,
                label=tr(this, "ui.t-password", "Password"),
                js_type="password",
                placeholder="default",
                width=10,
                onChange=this.set_pass,
                ),
                e(ui.Button, tr(this, "ui.b-connect", "Connect"), js_type="submit", primary=True),
                onSubmit=this.submit,
                loading=this.state.loading,
                ))

Page = createReactClass({
    'displayName': 'LoginPage',

    'getInitialState': lambda: {'user': None,
                                'pass': None,
                                'loading': False,
                                },
    'set_user': lambda ev, d: this.setState({'user':d.value}),
    'set_pass': lambda ev, d: this.setState({'pass':d.value}),
    'submit': submit,
    'connect': connect,
    'as_guest': lambda: this.connect({}),
    'on_handshake': on_handshake,

    'render': page_render
})

