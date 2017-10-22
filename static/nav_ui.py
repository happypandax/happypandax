__pragma__('alias', 'as_', 'as')
from react_utils import (h,e,
                        render,
                        React,
                        ReactDOM,
                        createReactClass,
                        NavLink)
from client import client
from state import state
from ui import ui
from i18n import tr
from utils import defined

def pref_server(props):
    cfg = props.cfg
    u_cfg = props.u_cfg
    items = []
    if defined(cfg.server):
        if defined(cfg.server.server_name):
            items.append(e(ui.Form.Group,
                           e(ui.Form.Input,
                            width=10,
                            label=tr(props.tab, "", "Server Name"),
                            placeholder=tr(props.tab, "", "Mom's basement"),
                            defaultValue=cfg.server.server_name,
                            onChange=lambda e: props.upd("server.server_name", e.target.value)
                           ))
                         )
        items.append(e(ui.Message, tr(props.tab, "",
                    "Changes below this message requires a server restart."), info=True))

        if defined(cfg.server.host) and defined(cfg.server.port):
            items.append(e(ui.Form.Group,
                           e(ui.Form.Input,
                             width=10,
                            label=tr(props.tab, "", "Host"),
                            placeholder="localhost",
                            defaultValue=cfg.server.host,
                            onChange=lambda e: props.upd("server.host", e.target.value)
                           ),
                           e(ui.Form.Input,
                             width=4,
                            label=tr(props.tab, "", "Port"),
                            placeholder="7007",
                            defaultValue=cfg.server.port,
                            onChange=lambda e: props.upd("server.port", int(e.target.value))
                           ),
                           )
                         )

    return e(ui.Segment,
            e(ui.Form,
             *items
             ),
            basic=True,
            )

def pref_client(props):
    cfg = props.cfg
    u_cfg = props.u_cfg
    items = []
    if defined(cfg.server):
        items.append(e(ui.Message, tr(props.tab, "",
                    "Changes below this message requires a server restart."), info=True))

        if defined(cfg.server.host_web) and defined(cfg.server.port_web):
            items.append(e(ui.Form.Group,
                           e(ui.Form.Input,
                             width=10,
                            label=tr(props.tab, "", "Host"),
                            placeholder="",
                            defaultValue=cfg.server.host_web,
                            onChange=lambda e: props.upd("server.host_web", e.target.value)
                           ),
                           e(ui.Form.Input,
                             width=4,
                            label=tr(props.tab, "", "Port"),
                            placeholder="7007",
                            defaultValue=cfg.server.port_web,
                            onChange=lambda e: props.upd("server.port_web", int(e.target.value))
                           ),
                           )
                         )

    return e(ui.Segment,
            e(ui.Form,
             *items
             ),
            basic=True,
            )

def preftab_get_config(data=None, error=None):
    if data is not None and not error:
        this.setState({"config":data})
    elif error:
        state.app.notif("Failed to retrieve configuration", level="warning")
    else:
        client.call_func("get_config", this.get_config)

__pragma__("kwargs")
def preftab_set_config(data=None, error=None, cfg={}):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to update setting", level="warning")
    else:
        client.call_func("set_config", preftab_set_config, cfg=cfg)
__pragma__("nokwargs")

def preftab_update_config(key, value):
    this.state.u_config[key] = value

def preftab_render():
    t_refresh = this.trigger_refresh
    upd_config = this.update_config
    set_config = this.set_config
    config = this.state.config
    u_cfg = this.state.u_config
    tab = this
    el = lambda x: e(x, u_cfg=u_cfg, tab=tab, cfg=config, refresh=t_refresh, upd=upd_config, set=set_config)

    return e(ui.Tab,
            panes=[
                {'menuItem': tr(this, "ui.mi-pref-general", "General"),},
                {'menuItem': tr(this, "ui.mi-pref-logins", "Logins"),},
                {'menuItem': tr(this, "ui.mi-pref-metadata", "Metadata"),},
                {'menuItem': tr(this, "ui.mi-pref-download", "Download"),},
                {'menuItem': tr(this, "ui.mi-pref-monitoring", "Monitoring"),},
                {'menuItem': tr(this, "ui.mi-pref-ignore", "Ignore"),},
                {'menuItem': tr(this, "ui.mi-pref-client", "Client"),
                    'render': lambda: el(pref_client)},
                {'menuItem': tr(this, "ui.mi-pref-server", "Server"),
                    'render': lambda: el(pref_server)},
                ],
            menu=e(ui.Menu, secondary=True, pointing=True))


PrefTab = createReactClass({
    'displayName': 'PrefTab',

    'getInitialState': lambda: {'config': {}, 'refresh':False, 'u_config':{}},

    'get_config': preftab_get_config,

    'set_config': lambda k, v: preftab_set_config(cfg={k:v}),

    'update_config': preftab_update_config,

    'trigger_refresh': lambda: this.setState({'refresh':True}),

    'componentDidMount': lambda: this.get_config(),

    'componentWillUnmount': lambda: all((preftab_set_config(cfg=this.state.u_config),
                                         client.call_func("save_config"),
                                         location.reload(False) if this.state.refresh else None)),

    'render': preftab_render
})


class MenuItem:
    __pragma__("kwargs")
    def __init__(self, name, t_id=None,
                 icon="", position="",
                 header=False, handler=None,
                 url=None, modal=None,
                 on_modal_open=None, on_modal_close=None):
        self.name = name
        self.icon = icon
        self.position = position
        self.header = header
        self.children = []
        self.handler = handler
        self.url = url
        self.t_id = t_id
        self.modal = modal
        self.on_modal_open = on_modal_open
        self.on_modal_close = on_modal_close
    __pragma__("nokwargs")

    __pragma__("tconv")
    def has_children(self):
        return bool(self.children)
    __pragma__("notconv")

def sidebar_nav_render():
    if False:
        nav_width = "very thin"
    else:
        nav_width = "thin"

    icon = False
    if nav_width == "very thin":
        icon = True

    def nav_toggle_handler(e, props):
        print(props)

    items = []
    items.append(MenuItem("", icon="sidebar", position="left", handler=this.props["toggler"]))

    items.append(MenuItem("Dashboard", "ui.mi-dashboard", icon="home", url="/dashboard", handler=this.props["toggler"]))
    items.append(MenuItem("Favorites", "ui.mi-favorites", icon="heart", url="/favorite", handler=this.props["toggler"]))
    items.append(MenuItem("Library", "ui.mi-library", icon="grid layout", url="/library", handler=this.props["toggler"]))
    items.append(MenuItem("Inbox", "ui.mi-inbox", icon="inbox", url="/inbox", handler=this.props["toggler"]))
    items.append(MenuItem("Management", "ui.mi-management", icon="cubes", url="/management", handler=this.props["toggler"]))
    #Note: Artists, Tags, Etc. Able to favorite artists and tags
    items.append(MenuItem("Downloads", "ui.mi-downloads", icon="tasks", url="/downloads", handler=this.props["toggler"]))
    pref_item = MenuItem("Preferences", "ui.mi-preferences",
                         modal=[
                             e(ui.Modal.Content,
                                e(ui.Header, icon="settings", content=tr(this, "ui.mi-preferences", "Preferences")),
                                e(PrefTab),
                                ),
                             ],
                         icon="settings", position="right", handler=this.props["toggler"])
    items.append(pref_item)

    about_item = MenuItem("About", "ui.mi-about",
                        modal=[
                             e(ui.Modal.Content,
                                e(ui.Header, icon="info", content=tr(this, "ui.mi-about", "About")),
                                e(ui.Tab,
                                panes=[
                                    {'menuItem': tr(this, "ui.mi-about-info", "Info"),},
                                    {'menuItem': tr(this, "ui.mi-about-plugins", "Plugins"),},
                                    {'menuItem': tr(this, "ui.mi-about-stats", "Statistics"),},
                                    {'menuItem': tr(this, "ui.mi-about-bug", "Report bug"),},
                                    ],
                                menu=e(ui.Menu, secondary=True, pointing=True)))
                             ],
                        icon="info", position="right", handler=this.props["toggler"])
    items.append(about_item)
    #about_item.children.append(MenuItem("Check for updates"))
    #about_item.children.append(MenuItem("Visit homepage"))

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

        item_children = (e(ui.Icon, js_name=menu_icon, className="left", size=icon_size), tr(this, x.t_id, menu_name) if not icon else "",)

        as_link = {}
        if x.url:
            as_link = {"as":NavLink, "to":x.url, "activeClassName":"active"}

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
                        visible=this.props.toggled,
                        icon=icon,
                        defaultActiveIndex=3,
                        size="small"
                        )

SideBarNav = createReactClass({
    'displayName': 'SideBarNav',

    'render': sidebar_nav_render
})

def menu_nav_render():
    items = []
    items.append(MenuItem("", icon="sidebar", position="left", header=True, handler=this.props["toggler"]))

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
                            e(ui.Icon, js_name=menu_icon, size=icon_size),
                            menu_name,
                            js_name=menu_name,
                            header=x.header,
                            onClick=x.handler,
                            index=n,
                            icon=not menu_name,
                            )
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
                        #fluid=True,
                        size="small",
                        stackable=True)

MenuNav = createReactClass({
    'displayName': 'MenuNav',

    'render': menu_nav_render
})
