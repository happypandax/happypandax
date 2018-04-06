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
                             )
from src.ui import ui, Alert, Notif, TitleChange
from src.nav import (sidebar, menu)
from src.pages import (api, collection, gallery,
                       dashboard, favorites, inbox,
                       library, page, directory,
                       downloads, login)
from src.client import pushclient, PushID
from src import utils
from org.transcrypt.stubs.browser import __pragma__

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Date = None
__pragma__('noskip')


__pragma__('alias', 'as_', 'as')
require('smoothscroll-polyfill').polyfill()

preview_txt = """Hi there!

This is a [preview] of what HPX is capable of.
Though, it is not a complete preview because I plan to keep adding more features over time.
This [preview] is intended for users migrating from good old Happypanda.
Why is that?
Well, because you won't be able to use HPX without a database from Happypanda.
HPX [preview] also means that it's not possible to write anything to the HPX database yet.
There is no "Add gallery..." function yet. I have not implemented it.
To use HPX you need to convert your database from Happypanda to a HPX database.
You can do that with the GUI (named 'happypandax_gui'), click the button named "HP to HPX".

I'd advise against deleting your Happypanda database. You will likely need to convert again in the future.
So, if you wish to add new galleries, a proposed way is:
Add galleries in Happypanda -> Convert database -> New galleries are in HPX

HPX has an auto update feature. When a new release comes out just click [Update] on the pop-up notification and it'll update and restart for you automatically!
(Provided you're not running from source).
HPX should gradually become much better than Happypanda. Now you can fa- I mean indulge your stuff from anywhere once you have it set up!

I have poured many hours into HPX and will likely continue to do so in the forseeable future!
I want to thank everyone who have contributed to HPX and HP in some way or another.
I want to especially thank you guys who went ahead and donated to me.
I did not actually expect anyone to do that so I am very happy, and most importantly, it motivated me a ton!
And so... because of that, I went ahead and made a Patreon. The Patreon will be for HPX and my art.
If you think that Happypanda has served you well and want to see HPX become better faster, please consider supporting me on there.
It'll motivate me a ton! :)

Once again, thank you guys who donated to me through Ko-Fi.

I hope you'll like HPX.
"""


def on_update(props):
    if props.location.pathname != this.props.location.pathname:
        for x in state.commands:
            x.stop()
        # HACK: blocks scroll restoration
        # TODO: scroll restoration
        window.scrollTo(0, 0)


def on_path_mount():
    state.history = this.props.history


PathChange = createReactClass({
    'displayName': 'PathChange',

    'componentWillReceiveProps': on_update,

    'componentDidMount': on_path_mount,

    'render': lambda: None
})

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
                if data['id'] in (PushID.Update,):
                    tmout = tmout * 1.5
                    ic = "angle double up"
                    if state.history:
                        utils.go_to(state.history, "/downloads")
                this.notif(data['body'], data['title'], icon=ic, timeout=tmout)
    elif error:
        this.notif("Failed to retrieve server notification", level="warning")
    else:
        if state['active'] and state['connected'] and state['accepted']:
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


def app_menu_contents(el, **kwargs):
    this.setState({'menu_nav_contents': el, 'menu_nav_args': kwargs})


__pragma__("nokwargs")


def app_render():

    if this.state.logged_in:
        sidebar_args = {
            'toggler': this.toggle_sidebar,
            'toggled': this.state["sidebar_toggled"]
        }

        menu_args = {
            'toggler': this.toggle_sidebar,
            'contents': this.state["menu_nav_contents"],
            'menu_args': this.state["menu_nav_args"]
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
        modal_els.append(e(ui.Modal,
                           e(ui.Modal.Header, dict(this.state.server_push_msg).get("title", '')),
                           e(ui.Modal.Content, dict(this.state.server_push_msg).get("body", '')),
                           *server_push_actions_el,
                           onClose=this.server_push_close,
                           open=this.state.server_push, dimmer="inverted", closeIcon=True)
                         )

        modal_els.append(e(ui.Modal,
                           e(ui.Modal.Header, "Welcome to HappyPanda X Preview!"),
                           e(ui.Modal.Content, preview_txt, style={"white-space": "pre-wrap"}),
                           e(ui.Modal.Actions, e(ui.Button, e(ui.Icon, js_name="heart"), "Show your support on patreon!",
                                                 href="https://www.patreon.com/twiddly", target="_blank", color="orange")),
                           closeIcon=True,
                           open=utils.storage.get("preview_msg", this.state.preview_msg),
                           onClose=this.close_preview_msg)
                         )

        api_route = []
        if this.state.debug:
            api_route.append(e(Route, path="/api", component=this.api_page))

        el = e(Router,
               h("div",
                 e(ui.Responsive,
                   #e(ConnectStatus, context=this.state.root_ref),
                   e(sidebar.SideBar, **sidebar_args), minWidth=767),
                 e(ui.Responsive,
                   e(sidebar.SideBar, mobile=True, **sidebar_args), maxWidth=768),
                 e(Route, component=PathChange),
                 e(ui.Ref,
                   e(ui.Sidebar.Pusher,
                     e(ui.Visibility,
                       e(ui.Responsive,
                         e(menu.Menu, **menu_args), minWidth=767),
                       e(ui.Responsive,
                         e(menu.Menu, mobile=True, **menu_args), maxWidth=768),
                       onBottomPassed=this.toggle_scroll_up,
                       once=False,
                       ),
                     e(Switch,
                       *api_route,
                       e(Route, path="/dashboard", component=this.dashboard_page),
                       e(Route, path="/library", component=this.library_page),
                       e(Route, path="/favorite", component=this.favorites_page),
                       e(Route, path="/inbox", component=this.inbox_page),
                       e(Route, path="/directory", component=this.directory_page),
                       e(Route, path="/downloads", component=this.downloads_page),
                       e(Route, path="/item/gallery", component=this.gallery_page),
                       e(Route, path="/item/collection", component=this.collection_page),
                       e(Route, path="/item/page", component=this.page_page),
                       e(Redirect, js_from="/", exact=True, to={'pathname': "/library"}),
                       ),
                     # e(ui.Sticky,
                     #  e(ui.Button, icon="chevron up", size="large", floated="right"),
                     #   bottomOffset=55,
                     #   context=this.state.container_ref,
                     #   className="foreground-sticky"),
                     e(ui.Dimmer, simple=True, onClickOutside=this.toggle_sidebar),
                     *modal_els,

                     dimmed=this.state.sidebar_toggled,
                     as_=ui.Dimmer.Dimmable,
                     className="min-fullheight",
                     ),
                   innerRef=this.get_context_ref,
                   ),
                 ),
               key="1",
               )
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
        "menu_nav_args": {},
        'server_push': False,
        'server_push_msg': {},
        'preview_msg': True,
        'scroll_up': False,
        'logged_in': js_undefined,
        'debug': state.debug,
    },

    'componentWillUnMount': app_will_unmount,
    'componentWillMount': app_will_mount,
    'componentDidMount': app_did_mount,

    'toggle_scroll_up': lambda: this.setState({'scroll_up': not this.state.scroll_up}),

    "notif": None,

    'close_preview_msg': lambda: all((this.setState({'preview_msg': False}),
                                      utils.storage.set("preview_msg", False))),

    'server_notifications': server_notifications,
    'server_push_close': lambda: this.setState({'server_push': False}),

    'on_login': lambda s: this.setState({'logged_in': s}),

    'toggle_sidebar': lambda: (this.setState({'sidebar_toggled': not this.state['sidebar_toggled']})),

    'set_menu_contents': app_menu_contents,
    'get_context_ref': get_container_ref,
    'get_root_ref': lambda c: this.setState({'root_ref': c}),

    'api_page': lambda p: e(api.Page, menu=this.set_menu_contents, **p),
    'dashboard_page': lambda p: e(dashboard.Page, menu=this.set_menu_contents, **p),
    'library_page': lambda p: e(library.Page, menu=this.set_menu_contents, **p),
    'favorites_page': lambda p: e(favorites.Page, menu=this.set_menu_contents, **p),
    'inbox_page': lambda p: e(inbox.Page, menu=this.set_menu_contents, **p),
    'page_page': lambda p: e(page.Page, menu=this.set_menu_contents, **p),
    'gallery_page': lambda p: e(gallery.Page, menu=this.set_menu_contents, **p),
    'collection_page': lambda p: e(collection.Page, menu=this.set_menu_contents, **p),
    'directory_page': lambda p: e(directory.Page, menu=this.set_menu_contents, **p),
    'downloads_page': lambda p: e(downloads.Page, menu=this.set_menu_contents, **p),

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

render(e(App), 'root')
