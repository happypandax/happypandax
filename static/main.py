__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         render,
                         React,
                         ReactDOM,
                         createReactClass,
                         Router,
                         Route,
                         Notif)
from ui import ui
import nav_ui
import api
import dashboard
import library

def on_mount():
    this.notif = this.refs.notif

def add_notif(o):
    this.notif.addNotification(o)

App = createReactClass({
    'displayName': 'App',


    'getInitialState': lambda: {
        "sidebar_toggled":True,
        "menu_nav_contents":None,
        },

    "notif":None,

    'add_notif': lambda o: add_notif,

    'componentDidMount': on_mount,

    'toggle_sidebar': lambda: (this.setState({'sidebar_toggled':not this.state['sidebar_toggled']})),

    'set_menu_contents': lambda c: (this.setState({'menu_nav_contents':c})),

    'api_page': lambda: e(api.Page, menu=this.set_menu_contents, notif=this.notif),
    'dashboard_page': lambda: e(dashboard.Page, menu=this.set_menu_contents, notif=this.notif),
    'library_page': lambda: e(library.Page, menu=this.set_menu_contents, notif=this.notif),

    'render': lambda: e(Router,
                        h("div",
                            #e(Notif, ref="notif"),
                            e(nav_ui.MenuNav, toggler=this.toggle_sidebar, contents=this.state["menu_nav_contents"]),
                            e(ui.Sidebar.Pushable,
                            e(nav_ui.SideBarNav, toggled=this.state["sidebar_toggled"]),
                            e(ui.Segment,
                            e(Route, path="/api", component=this.api_page),
                            e(Route, path="/dashboard", component=this.dashboard_page),
                            e(Route, path="/library", component=this.library_page),
                            className="sidebar-container",
                            basic=True),
                            as_=ui.Segment,
                            attached="bottom",
                            className="main-content"
                            ),
                            className="bodyheight"
                            )
                        )
})

render(e(App), 'root')