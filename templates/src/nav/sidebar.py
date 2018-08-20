from src.react_utils import (h, e,
                             createReactClass,
                             NavLink)
from src.ui import ui
from src.i18n import tr
from src.nav import MenuItem
from src.pages import preferences, about
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Object = Date = None
__pragma__('noskip')


def sidebar_nav_render():
    if this.props.mobile:
        nav_width = "very thin"
    else:
        nav_width = "thin"

    icon = False
    if nav_width == "very thin":
        icon = True

    def nav_toggle_handler(e, props):
        print(props)

    items = []
    items.append(MenuItem("", position="left", handler=this.props["toggler"],
                          content=e(ui.Icon, className="hpx-alternative huge left")))

    items.append(
        MenuItem(
            "Manage",
            "ui.mi-manage",
            icon="plus square outline",
            url="/manage",
            position="left",
            handler=this.props["toggler"]))

    #items.append(MenuItem("Dashboard", "ui.mi-dashboard", icon="home", url="/dashboard", handler=this.props["toggler"]))
    items.append(MenuItem("Favorites", "ui.mi-favorites", icon="heart", url="/favorite", handler=this.props["toggler"]))
    items.append(
        MenuItem(
            "Library",
            "ui.mi-browse",
            icon="grid layout",
            url="/library",
            handler=this.props["toggler"]))
    items.append(
        MenuItem(
            "directory",
            "ui.mi-directory",
            icon="cubes",
            url="/directory",
            handler=this.props["toggler"]))
    # Note: Artists, Tags, Etc. Able to favorite artists and tags
    items.append(
        MenuItem(
            "Activity",
            "ui.mi-activity",
            icon="tasks",
            url="/activity",
            handler=this.props["toggler"]))
    pref_item = MenuItem("Preferences", "ui.mi-preferences",
                         modal=[
                             e(ui.Modal.Content,
                               e(ui.Header, icon="settings", content=tr(this, "ui.mi-preferences", "Preferences")),
                               e(preferences.PrefTab),
                               ),
                         ],
                         icon="settings", position="right", handler=this.props["toggler"])
    items.append(pref_item)

    about_item = MenuItem("About", "ui.mi-about",
                          modal=[
                              e(ui.Modal.Content,
                                e(ui.Header, icon="info", content=tr(this, "ui.mi-about", "About")),
                                e(about.AboutTab),
                                )
                          ],
                          icon="info", position="right", handler=this.props["toggler"])
    items.append(about_item)

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

        content = tr(this, x.t_id, menu_name) if x.content is None else x.content

        item_children = []

        if menu_icon:
            item_children.append(e(ui.Icon, js_name=menu_icon, className="left", size=icon_size))

        item_children.append(content if not icon else "")

        as_link = {}
        if x.url:
            as_link = {"as": NavLink, "to": x.url, "activeClassName": "active"}

        menu_el = e(ui.Menu.Item,
                    *item_children,
                    js_name=menu_name,
                    header=x.header,
                    onClick=x.handler,
                    index=n,
                    icon=not menu_name,
                    **as_link)
        if x.modal:
            menu_el = e(ui.Modal, *x.modal,
                        trigger=menu_el,
                        dimmer="inverted",
                        closeIcon=True,
                        onClose=x.on_modal_close,
                        onOpen=x.on_modal_open,
                        centered=False,
                        className="min-400-h"
                        )

        container.append(menu_el)

    cnt_el = h("div",
               h("div",
                 *elements_left,
                 className="top-aligned"),
               h("div",
                 *elements,
                 className="middle-aligned"),
               h("div",
                 *elements_right,
                 className="bottom-aligned"),
               className="flex-container")

    el_args = {'as': ui.Menu,
               'animation': "overlay",
               'width': nav_width,
               'vertical': True,
               'visible': this.props.toggled,
               'icon': icon,
               'defaultActiveIndex': 3,
               'size': "small",
               'className': "window-height",
               'inverted': True}

    if this.props.mobile:
        el_args['direction'] = "right"

    return e(ui.Sidebar, cnt_el, **el_args)


SideBar = createReactClass({
    'displayName': 'SideBar',

    'render': sidebar_nav_render
})
