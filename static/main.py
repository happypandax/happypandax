__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         render,
                         React,
                         ReactDOM,
                         createReactClass,
                         Router,
                         Route,
                         )
from ui import ui, Alert, Notif
from state import state
import nav_ui
import api
import dashboard
import library
import favorites
import inbox

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
        _timeout = 8000
    else:
        _a = Alert.info

    kw = dict({
        "customFields": {
            "content":msg,
            "header":header,
            "mskwargs":{level:True, "icon":icon}
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


def app_render():
    #state.app = this
    return e(Router,
            h("div",
                e(nav_ui.MenuNav, toggler=this.toggle_sidebar, contents=this.state["menu_nav_contents"]),
                e(ui.Sidebar.Pushable,
                e(nav_ui.SideBarNav, toggled=this.state["sidebar_toggled"]),
                e(ui.Segment,
                e(Route, path="/api", component=this.api_page),
                e(Route, path="/dashboard", component=this.dashboard_page),
                e(Route, path="/library", component=this.library_page),
                e(Route, path="/favorite", component=this.favorites_page),
                e(Route, path="/inbox", component=this.inbox_page),
                className="sidebar-container",
                basic=True),
                as_=ui.Segment,
                attached="bottom",
                className="main-content"
                ),
                e(Alert, contentTemplate=Notif, stack={'limit':6, 'spacing':20}, position="top-right", effect="slide", offset=50),
                className="bodyheight"
                )
            )

App = createReactClass({
    'displayName': 'App',


    'getInitialState': lambda: {
        "sidebar_toggled":True,
        "menu_nav_contents":None,
        },

    'componentWillMount': app_will_mount,

    "notif":None,

    'add_notif': lambda o: add_notif,

    'toggle_sidebar': lambda: (this.setState({'sidebar_toggled':not this.state['sidebar_toggled']})),

    'set_menu_contents': lambda c: (this.setState({'menu_nav_contents':c})),

    'api_page': lambda: e(api.Page, menu=this.set_menu_contents),
    'dashboard_page': lambda: e(dashboard.Page, menu=this.set_menu_contents),
    'library_page': lambda: e(library.Page, menu=this.set_menu_contents),
    'favorites_page': lambda: e(favorites.Page, menu=this.set_menu_contents),
    'inbox_page': lambda: e(inbox.Page, menu=this.set_menu_contents),

    'render': app_render,
})

render(e(App), 'root')