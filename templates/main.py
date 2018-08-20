from src.state import state
from src.react_utils import (h,
                             e,
                             render,
                             Switch,
                             ReactDOM,
                             createReactClass,
                             Router,
                             Route,
                             Redirect,
                             withRouter,
                             )
from src.ui import ui, Alert, Notif, TitleChange
from src.nav import (sidebar, menu)
from src.i18n import tr
from src.pages import (api, collection, gallery,
                       dashboard, favorites, library,
                       page, directory,
                       activity, login, manage)
from src.client import pushclient, PushID
from src import utils
from org.transcrypt.stubs.browser import __pragma__

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
screen = Object = Date = None
__pragma__('noskip')


__pragma__('alias', 'as_', 'as')
require('smoothscroll-polyfill').polyfill()


def on_update(props):
    if props.location.pathname != this.props.location.pathname:
        for x in state.commands:
            if x.daemon:
                x.stop()
        # HACK: blocks scroll restoration
        # TODO: scroll restoration
        if state.reset_scroll:
            window.scrollTo(0, 0)


def on_path_mount():
    state.history = this.props.history


PathChange = createReactClass({
    'displayName': 'PathChange',

    'componentWillReceiveProps': on_update,

    'componentDidMount': on_path_mount,

    'render': lambda: None
}, pure=True)

__pragma__("kwargs")


def notif(msg, header="", level="info", icon=None, **kwargs):
    _a = None
    _timeout = 5000
    if level == "warning":
        _a = Alert.warning
        _timeout = _timeout * 1.3
    elif level == "success":
        _a = Alert.success
    elif level == "error":
        _a = Alert.error
        _timeout = _timeout * 1.6
    else:
        _a = Alert.info

    kw = dict({
        "customFields": {
            "content": msg,
            "header": header,
            "mskwargs": {level: True,
                         "icon": icon,
                         "style": {"whiteSpace": "pre-wrap"}
                         }
        },
        "timeout": _timeout
    })
    kw.update(kwargs)

    aid = _a("", kw)
    return aid


__pragma__("nokwargs")

state['notif'] = notif

__pragma__("tconv")


def server_notifications(data=js_undefined, error=None):
    if data is not js_undefined and not error:
        if data:
            if data.actions:
                this.setState({'server_push_msg': data, 'server_push': True})
            else:
                tmout = 20000
                ic = "info"
                msg = data['body']
                if data['id'] in (PushID.Update,):
                    tmout = tmout * 1.5
                    ic = "angle double up"
                    if state.history:
                        utils.go_to(state.history, "/activity")
                    this.notif(tr(None, "ui.t-changelog-location", "About -> Changelog"),
                               data['title'], icon=ic, timeout=tmout)
                this.notif(msg, data['title'], icon=ic, timeout=tmout)
    elif error:
        this.notif("Failed to retrieve server notification", level="warning")
    else:
        if state['active'] and state['connected'] and state['accepted'] and utils.storage.get(
                "ping_for_notifications", True):
            pushclient.call_func("get_notification", this.server_notifications)


__pragma__("notconv")

__pragma__("kwargs")


def server_notifications_reply(data=None, error=None, msg_id=0, values={}):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to reply to server notification", level="warning")
    else:
        pushclient.call_func("reply_notification",
                             server_notifications_reply,
                             msg_id=msg_id,
                             action_values=values
                             )


__pragma__("nokwargs")


def page_visibility_update(e, d):
    calc = d.calculations
    can_fix_menu = this.state.fixable_menu and window.matchMedia("(min-width: 768px)").matches
    if calc.pixelsPassed > 80 and can_fix_menu:
        this.setState({'fixed_menu': True})
    elif calc.pixelsPassed < 80 and calc.direction == "up" and can_fix_menu:
        if calc.pixelsPassed < 20:
            this.setState({'fixed_menu': False})
    else:
        this.setState({'fixed_menu': False})

    if calc.pixelsPassed > 500:
        this.setState({'scroll_up_sticky': True})
    elif calc.pixelsPassed < 500 and calc.pixelsPassed > 50 and calc.direction == "up":
        pass
    else:
        this.setState({'scroll_up_sticky': False})


def app_will_mount():
    state['app'] = this
    this.notif = notif


def app_did_mount():
    utils.interval_func(this.server_notifications, 5000)
    document.body.appendChild(this.state.portal_el)


def app_will_unmount():
    document.body.removeChild(this.state.portal_el)


def get_container_ref(ctx):
    state['container_ref'] = ctx
    this.setState({'container_ref': ctx})


__pragma__("kwargs")


def app_menu_contents(el, fixed=False, **kwargs):
    this.setState({'menu_nav_contents': el,
                   'menu_nav_args': kwargs,
                   'fixable_menu': fixed})


__pragma__("nokwargs")


def app_render():

    if this.state.logged_in:
        sidebar_args = {
            'location': this.props.location,
            'toggler': this.toggle_sidebar,
            'toggled': this.state["sidebar_toggled"],
        }

        menu_args = {
            'location': this.props.location,
            'toggler': this.toggle_sidebar,
            'contents': this.state["menu_nav_contents"],
            'menu_args': this.state["menu_nav_args"],
            'fixed': this.state.fixed_menu,
        }

        server_push_close = this.server_push_close
        server_push_actions_el = []
        if dict(this.state.server_push_msg).get("actions", False):
            server_push_actions = []
            push_id = this.state.server_push_msg['id']
            for a in this.state.server_push_msg['actions']:
                a_id = a['id']
                if a['type'] == 'button':
                    server_push_actions.append(
                        e(ui.Button, a['text'],
                          value=a_id,
                          onClick=lambda ev, da: all((
                              server_notifications_reply(msg_id=push_id, values={da.value: da.value}),
                              server_push_close()))))

            server_push_actions_el.append(e(ui.Modal.Actions, *server_push_actions))

        modal_els = []
        server_push_msg = dict(this.state.server_push_msg)
        push_body = server_push_msg.get("body", '')
        if server_push_msg['id'] in (PushID.Update,):
            push_body = tr(None, "ui.t-changelog-location", "About -> Changelog") + '\n' + push_body

        modal_els.append(e(ui.Modal,
                           e(ui.Modal.Header, server_push_msg.get("title", '')),
                           e(ui.Modal.Content, push_body, style={"whiteSpace": "pre-wrap"}),
                           *server_push_actions_el,
                           onClose=this.server_push_close,
                           open=this.state.server_push, dimmer="inverted", closeIcon=True)
                         )

        api_route = []
        if this.state.debug:
            api_route.append(e(Route, path="/api", component=this.api_page))

        el = h("div",
               e(ui.Responsive,
                   #e(ConnectStatus, context=this.state.root_ref),
                   e(sidebar.SideBar, **sidebar_args), minWidth=767),
               e(ui.Responsive,
                   e(sidebar.SideBar, mobile=True, **sidebar_args), maxWidth=768),
               e(Route, component=PathChange),
               e(ui.Ref,
                   e(ui.Sidebar.Pusher,
                     h("div", className="ui secondary menu" if this.state.fixed_menu else ""),
                     e(ui.Responsive,
                       e(menu.Menu, **menu_args), minWidth=767),
                     e(ui.Responsive,
                       e(menu.Menu, mobile=True, **menu_args), maxWidth=768),
                     e(ui.Visibility,
                         e(Switch,
                           *api_route,
                           e(Route, path="/manage", component=this.manage_page),
                           e(Route, path="/dashboard", component=this.dashboard_page),
                           e(Route, path="/library", component=this.library_page),
                           e(Route, path="/favorite", component=this.favorites_page),
                           e(Route, path="/directory", component=this.directory_page),
                           e(Route, path="/activity", component=this.activity_page),
                           e(Route, path="/item/gallery/:gallery_id(\d+)/page/:page_number(\d+)", component=this.page_page),
                           e(Route, path="/item/gallery/:item_id(\d+)", component=this.gallery_page),
                           e(Route, path="/item/collection/:item_id(\d+)", component=this.collection_page),
                           e(Redirect, js_from="/", exact=True, to={'pathname': "/library"}),
                           ),
                       onUpdate=this.page_visibility_update,
                       ),
                     e(ui.Portal,
                       e(ui.Button,
                         onClick=utils.scroll_to_top,
                         basic=True,
                         icon="chevron up",
                         size="small",
                         className="bottom-right-sticky"),
                       open=this.state.scroll_up_sticky,
                       ),
                     e(ui.Dimmer, simple=True, onClickOutside=this.toggle_sidebar),
                     *modal_els,

                     dimmed=this.state.sidebar_toggled,
                     as_=ui.Dimmer.Dimmable,
                     className="force-viewport-size",
                     ),
                   innerRef=this.get_context_ref,
                 ),
               key="1",
               ),
    elif not utils.defined(this.state.logged_in):
        el = e(ui.Segment,
               e(ui.Dimmer,
                   e(ui.Loader),
                   active=True),
               basic=True,
               className="fullheight",
               key="1",
               )
    else:
        el = e(login.Page, on_login=this.on_login, key="1"),

    alert_el = e(Alert, contentTemplate=Notif, stack={'limit': 6, 'spacing': 20},
                 position="top-right", effect="slide", offset=50,
                 preserveContext=True, key="2",
                 )

    return [e(TitleChange), el, ReactDOM.createPortal(alert_el, this.state.portal_el)]


App = createReactClass({
    'displayName': 'App',


    'getInitialState': lambda: {
        "portal_el": document.createElement('div'),
        "root_ref": None,
        "container_ref": None,
        "sidebar_toggled": False,
        "menu_nav_contents": None,
        "fixed_menu": False,
        "fixable_menu": False,
        "scroll_up_sticky": False,
        "menu_nav_args": {},
        'server_push': False,
        'server_push_msg': {},
        'preview_msg': True,
        'logged_in': js_undefined,
        'debug': state.debug,
        "changelog": "",
    },

    'componentWillUnMount': app_will_unmount,
    'componentWillMount': app_will_mount,
    'componentDidMount': app_did_mount,

    "notif": None,

    'close_preview_msg': lambda: all((this.setState({'preview_msg': False}),
                                      utils.storage.set("preview_msg", False))),

    'server_notifications': server_notifications,
    'server_push_close': lambda: this.setState({'server_push': False}),

    'on_login': lambda s: this.setState({'logged_in': s}),

    'toggle_sidebar': lambda: (this.setState({'sidebar_toggled': not this.state['sidebar_toggled']})),
    'page_visibility_update': page_visibility_update,
    'set_menu_contents': app_menu_contents,
    'get_context_ref': get_container_ref,
    'get_root_ref': lambda c: this.setState({'root_ref': c}),

    'api_page': lambda p: e(api.Page, menu=this.set_menu_contents, **p),
    'dashboard_page': lambda p: e(dashboard.Page, menu=this.set_menu_contents, **p),
    'library_page': lambda p: e(library.Page, menu=this.set_menu_contents, **p),
    'favorites_page': lambda p: e(favorites.Page, menu=this.set_menu_contents, **p),
    'page_page': lambda p: e(page.Page, menu=this.set_menu_contents, **p),
    'gallery_page': lambda p: e(gallery.Page, menu=this.set_menu_contents, **p),
    'collection_page': lambda p: e(collection.Page, menu=this.set_menu_contents, **p),
    'directory_page': lambda p: e(directory.Page, menu=this.set_menu_contents, **p),
    'activity_page': lambda p: e(activity.Page, menu=this.set_menu_contents, **p),
    'manage_page': lambda p: e(manage.Page, menu=this.set_menu_contents, **p),

    'render': app_render,
})

vkeys = utils.visibility_keys()


def visibility_change():
    if document[vkeys['hidden']]:
        state['active'] = False
    else:
        state['active'] = True


# todo: check support
document.addEventListener(vkeys['visibilitychange'], visibility_change, False)

render(e(Router, e(withRouter(App))), 'root')
