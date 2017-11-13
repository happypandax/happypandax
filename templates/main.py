__pragma__('alias', 'as_', 'as')
require('smoothscroll-polyfill').polyfill();
from src.state import state
from src.react_utils import (h,
                             e,
                             render,
                             React,
                             ReactDOM,
                             createReactClass,
                             Router,
                             Route,
                             withRouter
                             )
from src.ui import ui, Alert, Notif
from src.nav import (sidebar, menu)
from src.pages import (api, collection, gallery,
                       dashboard, favorites, inbox,
                       library, page)


def on_update(props):
    if props.location.pathname != this.props.location.pathname:
        for x in state.commands:
            x.stop()

PathChange = createReactClass({
    'displayName': 'PathChange',

    'componentWillReceiveProps': on_update,

    'render': lambda: None
})

__pragma__("kwargs")


def notif(msg, header="", level="info", icon=None, **kwargs):
    _a = None
    _timeout = 5000
    if level == "warning":
        _a = Alert.warning
    elif level == "success":
        _a = Alert.success
    elif level == "error":
        _a = Alert.error
        _timeout = _timeout * 2
    else:
        _a = Alert.info

    kw = dict({
        "customFields": {
            "content": msg,
            "header": header,
            "mskwargs": {level: True, "icon": icon}
        },
        "timeout": _timeout
    })
    kw.update(kwargs)

    aid = _a("", kw)
    return aid
__pragma__("nokwargs")

state['notif'] = notif


def app_will_mount():
    state['app'] = this
    this.notif = notif


def get_container_ref(ctx):
    state['container_ref'] = ctx

def app_render():
    return e(Router,
               e(ui.Sidebar.Pushable,
                 e(sidebar.SideBar, toggler=this.toggle_sidebar, toggled=this.state["sidebar_toggled"]),
                 e(Route, component=PathChange),
                 e(Alert, contentTemplate=Notif, stack={'limit': 6, 'spacing': 20},
                   position="top-right", effect="slide", offset=50),
                e(ui.Ref,
                    e(ui.Sidebar.Pusher,
                    e(menu.Menu, toggler=this.toggle_sidebar, contents=this.state["menu_nav_contents"]),
                    e(Route, path="/api", component=this.api_page),
                    e(Route, path="/dashboard", component=this.dashboard_page),
                    e(Route, path="/", exact=True, component=this.library_page),
                    e(Route, path="/library", component=this.library_page),
                    e(Route, path="/favorite", component=this.favorites_page),
                    e(Route, path="/inbox", component=this.inbox_page),
                    e(Route, path="/item/gallery", component=this.gallery_page),
                    e(Route, path="/item/collection", component=this.collection_page),
                    e(Route, path="/item/page", component=this.page_page),
                    dimmed=this.state.sidebar_toggled,
                    ),
                    innerRef=this.get_context_ref,
                    ),
                className="main-content",
                 ),
             )

App = createReactClass({
    'displayName': 'App',


    'getInitialState': lambda: {
        "sidebar_toggled": False,
        "menu_nav_contents": None,
    },

    'componentWillMount': app_will_mount,

    "notif": None,

    'add_notif': lambda o: add_notif,

    'toggle_sidebar': lambda: (this.setState({'sidebar_toggled': not this.state['sidebar_toggled']})),

    'set_menu_contents': lambda c: (this.setState({'menu_nav_contents': c})),
    'get_context_ref': get_container_ref,

    'api_page': lambda p: e(api.Page, menu=this.set_menu_contents, **p),
    'dashboard_page': lambda p: e(dashboard.Page, menu=this.set_menu_contents, **p),
    'library_page': lambda p: e(library.Page, menu=this.set_menu_contents, **p),
    'favorites_page': lambda p: e(favorites.Page, menu=this.set_menu_contents, **p),
    'inbox_page': lambda p: e(inbox.Page, menu=this.set_menu_contents, **p),
    'page_page': lambda p: e(page.Page, menu=this.set_menu_contents, **p),
    'gallery_page': lambda p: e(gallery.Page, menu=this.set_menu_contents, **p),
    'collection_page': lambda p: e(collection.Page, menu=this.set_menu_contents, **p),

    'render': app_render,
})

render(e(App), 'root')
