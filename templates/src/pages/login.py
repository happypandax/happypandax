from src.react_utils import (e, h,
                             createReactClass)
from src.ui import ui, TitleChange
from src.state import state
from src.i18n import tr
from src.utils import defined
from src.client import client
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Date = None
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
        this.setState({'loading': True})


def on_handshake(msg):
    this.setState({'loading': False, 'accepted': bool(msg['accepted'])})
    if this.props.on_login:
        this.props.on_login(msg['accepted'])


def page_render():
    els = []
    if state['guest_allowed']:
        els.append(e(ui.Button, tr(this, "ui.t-continue-as-guest", "Connect as guest"),
                     fluid=True, primary=True, onClick=this.as_guest))
        els.append(e(ui.Divider, tr(this, "ui.t-or", "Or"), horizontal=True))

    return e(ui.Grid,
             e(TitleChange, title=tr(this, "ui.t-login", "Login")),
             e(ui.Grid.Row),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Segment,
                   this.props.children,
                   h("center", e(ui.Icon, className="hpx-standard", size="massive")),
                   e(ui.Divider, hidden=True, horizontal=True),
                   *els,
                   e(ui.Form,
                     e(ui.Form.Input,
                       label=tr(this, "ui.t-username", "Username"),
                       placeholder="default",
                       onChange=this.set_user,
                       error=not this.state.accepted if defined(this.state.accepted) else this.state.accepted,
                       ),
                     e(ui.Form.Input,
                       label=tr(this, "ui.t-password", "Password"),
                       js_type="password",
                       placeholder="default",
                       onChange=this.set_pass,
                       error=not this.state.accepted if defined(this.state.accepted) else this.state.accepted,
                       ),
                     e(ui.Message, tr(this, "ui.t-wrong-credentials", "Wrong credentials!"), error=True),
                     e(ui.Button, tr(this, "ui.b-connect", "Connect"),
                       js_type="submit", primary=True, floated="right"),
                     onSubmit=this.submit,
                     loading=this.state.loading,
                     error=not this.state.accepted if defined(this.state.accepted) else this.state.accepted,
                     ),
                   clearing=True,
                   ),
                 width="7",
                 widescreen="3",
                 largescreen="4",
                 mobile="15",
                 tablet="9",
                 computer="7",
                 )),
             e(ui.Grid.Row),
             verticalAlign="middle",
             centered=True,
             className="fullheight"
             )


Page = createReactClass({
    'displayName': 'LoginPage',

    'getInitialState': lambda: {'user': None,
                                'pass': None,
                                'loading': False,
                                'accepted': js_undefined,
                                },
    'set_user': lambda ev, d: this.setState({'user': d.value}),
    'set_pass': lambda ev, d: this.setState({'pass': d.value}),
    'submit': submit,
    'connect': connect,
    'as_guest': lambda: this.connect({}),
    'on_handshake': on_handshake,

    'render': page_render
}, pure=True)
