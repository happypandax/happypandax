__pragma__('alias', 'as_', 'as')
from react_utils import (h,e,
                        render,
                        React,
                        ReactDOM,
                        createReactClass,
                        NavLink)

from ui import ui
from i18n import tr

class MenuItem:
    __pragma__("kwargs")
    def __init__(self, name, t_id=None, icon="", position="", header=False, handler=None, url=None, modal=None):
        self.name = name
        self.icon = icon
        self.position = position
        self.header = header
        self.children = []
        self.handler = handler
        self.url = url
        self.t_id = t_id
        self.modal = modal
    __pragma__("nokwargs")

    __pragma__("tconv")
    def has_children(self):
        return bool(self.children)
    __pragma__("notconv")

def sidebar_nav_render():
    if this.props['toggled']:
        nav_width = "very thin"
    else:
        nav_width = "thin"

    icon = False
    if nav_width == "very thin":
        icon = True

    def nav_toggle_handler(e, props):
        print(props)

    items = []
    items.append(MenuItem("Dashboard", "ui.mi-dashboard", icon="home", url="/dashboard"))
    items.append(MenuItem("Favorites", "ui.mi-favorites", icon="heart", url="/favorite"))
    items.append(MenuItem("Library", "ui.mi-library", icon="grid layout", url="/library"))
    items.append(MenuItem("Inbox", "ui.mi-inbox", icon="inbox", url="/inbox"))
    items.append(MenuItem("Downloads", "ui.mi-downloads", icon="tasks", url="/downloads"))
    pref_item = MenuItem("Preferences", "ui.mi-preferences",
                         modal=[e(ui.Modal.Header, tr(this, "ui.mi-preferences", "Preferences"))],
                         icon="settings", position="right")
    items.append(pref_item)
    pref_item.children.append(MenuItem("General"))
    pref_item.children.append(MenuItem("Logins"))
    pref_item.children.append(MenuItem("Metadata"))
    pref_item.children.append(MenuItem("Download"))
    pref_item.children.append(MenuItem("Monitoring"))
    pref_item.children.append(MenuItem("Ignoring"))
    pref_item.children.append(MenuItem("Client"))
    pref_item.children.append(MenuItem("Server"))

    about_item = MenuItem("About", "ui.mi-about",
                        modal=[e(ui.Modal.Header, tr(this, "ui.mi-about", "About"))],
                        icon="info", position="right")
    items.append(about_item)
    about_item.children.append(MenuItem("Plugins"))
    about_item.children.append(MenuItem("Statistics"))
    about_item.children.append(MenuItem("Help"))
    about_item.children.append(MenuItem("Check for updates"))
    about_item.children.append(MenuItem("Report bug"))
    about_item.children.append(MenuItem("Visit homepage"))

    elements = []
    elements_left = []
    elements_right = []
    for n, x in enumerate(items, 1):
        menu_name = x.name
        menu_icon = x.icon
        icon_size = "large"
        if icon:
            menu_name = ""

        if x.position == "right":
            container = elements_right
        elif x.position == "left":
            container = elements_left
        else:
            container = elements

        item_children = (e(ui.Icon, js_name=menu_icon, className="left medium-size", size=icon_size), tr(this, x.t_id, menu_name) if not icon else "",)

        as_link = {}
        if x.url:
            as_link = {"as":NavLink, "to":x.url, "activeClassName":"active"}

        menu_el = e(ui.Menu.Item,
                            *item_children,
                            js_name=menu_name,
                            header=x.header,
                            onClick=x.handler,
                            index=n,
                            **as_link)
        if x.modal:
            menu_el = e(ui.Modal, *x.modal,
                        trigger=menu_el,
                        )

        container.append(menu_el)

    return e(ui.Sidebar,
                        h("div",
                        h("div",
                            *elements_left,
                            className="top-aligned"),
                        h("div",
                            *elements,
                            className="middle-aligned"),
                        h("div",
                            *elements_right,
                            className="bottom-aligned"),
                        className="flex-container"),
                        as_=ui.Menu,
                        animation="push",
                        width=nav_width,
                        vertical=True,
                        visible=True,
                        icon=icon,
                        defaultActiveIndex=3,
                        className="sidebar-nav",
                        size="small"
                        )

SideBarNav = createReactClass({
    'displayName': 'SideBarNav',

    'render': sidebar_nav_render
})

def menu_nav_render():
    items = []
    items.append(MenuItem("HPX", icon="sidebar", position="left", header=True, handler=this.props["toggler"]))

    elements = []
    elements_left = []
    elements_right = []
    for n, x in enumerate(items, 1):
        menu_name = x.name
        menu_icon = x.icon
        icon_size = "large"

        if x.position == "right":
            container = elements_right
        elif x.position == "left":
            container = elements_left
        else:
            container = elements

        children = []
        for c in x.children:
            children.append(e(ui.Dropdown.Item, c.name))

        container.append(e(ui.Menu.Item,
                            e(ui.Icon, js_name=menu_icon, size=icon_size, className="medium-size"),
                            menu_name,
                            js_name=menu_name,
                            header=x.header,
                            onClick=x.handler,
                            index=n)
                         )
    menu_contents = this.props.contents
    if not isinstance(menu_contents, list):
        menu_contents = [menu_contents]
    return e(ui.Menu,
                        *elements_left,
                        *elements,
                        *menu_contents,
                        *elements_right,
                        secondary=True,
                        attached="top",
                        fluid=True,
                        size="small",
                        stackable=True)

MenuNav = createReactClass({
    'displayName': 'MenuNav',

    'render': menu_nav_render
})
