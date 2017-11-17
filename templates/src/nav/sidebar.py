__pragma__('alias', 'as_', 'as')
from src.react_utils import (h, e,
                             render,
                             React,
                             ReactDOM,
                             createReactClass,
                             NavLink)
from src.client import client
from src.state import state
from src.ui import ui
from src.i18n import tr
from src.utils import defined, is_same_machine
from src.nav import MenuItem

def pref_general(props):
    cfg = props.cfg
    u_cfg = props.u_cfg
    items = []
    if defined(cfg.gallery):
        
        if defined(cfg.gallery.external_image_viewer):

            if not is_same_machine():
                items.append(e(ui.Message, tr(props.tab, "",
                                            "Disabled because this client is connecting from a different device"), color="yellow"))

            items.append(e(ui.Form.Input,
                             width=16,
                             label=tr(props.tab, "", "External Image Viewer"),
                             placeholder=tr(props.tab, "", "path/to/executable"),
                             defaultValue=cfg.gallery.external_image_viewer,
                             onChange=lambda e: props.upd("gallery.external_image_viewer", e.target.value),
                             disabled=not is_same_machine(),
                             )
                         )
        if defined(cfg.gallery.external_image_viewer_args):
            items.append(e(ui.Form.Input,
                             width=8,
                             label=tr(props.tab, "", "External Image Viewer Arguments"),
                             placeholder=tr(props.tab, "", "example: -a -X --force"),
                             defaultValue=cfg.gallery.external_image_viewer_args,
                             onChange=lambda e: props.upd("gallery.external_image_viewer_args", e.target.value),
                             disabled=not is_same_machine(),
                             )
                         )

        if defined(cfg.gallery.send_path_to_first_file):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Send path to first file in folder/acrhive"),
                             defaultChecked=cfg.gallery.send_path_to_first_file,
                             onChange=lambda e, d: props.upd("gallery.send_path_to_first_file", d.checked),
                             disabled=not is_same_machine(),
                             ))
                         )

        items.append(e(ui.Divider, section=True))

    return e(ui.Segment,
             e(ui.Form,
               *items
               ),
             basic=True,
             )

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
                                      "Changes below this message require a server restart."), info=True))

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
                                      "Changes below this message require a server restart."), info=True))

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
        this.setState({"config": data})
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

    def el(x): return e(x, u_cfg=u_cfg, tab=tab, cfg=config, refresh=t_refresh, upd=upd_config, set=set_config)

    return e(ui.Tab,
             panes=[
                 {'menuItem': tr(this, "ui.mi-pref-general", "General"),
                  'render': lambda: el(pref_general)},
                 {'menuItem': tr(this, "ui.mi-pref-logins", "Logins"), },
                 {'menuItem': tr(this, "ui.mi-pref-metadata", "Metadata"), },
                 {'menuItem': tr(this, "ui.mi-pref-download", "Download"), },
                 {'menuItem': tr(this, "ui.mi-pref-monitoring", "Monitoring"), },
                 {'menuItem': tr(this, "ui.mi-pref-ignore", "Ignore"), },
                 {'menuItem': tr(this, "ui.mi-pref-client", "Client"),
                  'render': lambda: el(pref_client)},
                 {'menuItem': tr(this, "ui.mi-pref-server", "Server"),
                  'render': lambda: el(pref_server)},
             ],
             menu=e(ui.Menu, secondary=True, pointing=True))


PrefTab = createReactClass({
    'displayName': 'PrefTab',

    'getInitialState': lambda: {'config': {}, 'refresh': False, 'u_config': {}},

    'get_config': preftab_get_config,

    'set_config': lambda k, v: preftab_set_config(cfg={k: v}),

    'update_config': preftab_update_config,

    'trigger_refresh': lambda: this.setState({'refresh': True}),

    'componentDidMount': lambda: this.get_config(),

    'componentWillUnmount': lambda: all((preftab_set_config(cfg=this.state.u_config),
                                         client.call_func("save_config"),
                                         location.reload(False) if this.state.refresh else None)),

    'render': preftab_render
})

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
    items.append(MenuItem("", icon="sidebar", position="left", handler=this.props["toggler"]))

    #items.append(MenuItem("Dashboard", "ui.mi-dashboard", icon="home", url="/dashboard", handler=this.props["toggler"]))
    items.append(MenuItem("Favorites", "ui.mi-favorites", icon="heart", url="/favorite", handler=this.props["toggler"]))
    items.append(
        MenuItem(
            "Library",
            "ui.mi-library",
            icon="grid layout",
            url="/library",
            handler=this.props["toggler"]))
    items.append(MenuItem("Inbox", "ui.mi-inbox", icon="inbox", url="/inbox", handler=this.props["toggler"]))
    items.append(
        MenuItem(
            "Management",
            "ui.mi-management",
            icon="cubes",
            url="/management",
            handler=this.props["toggler"]))
    # Note: Artists, Tags, Etc. Able to favorite artists and tags
    items.append(
        MenuItem(
            "Downloads",
            "ui.mi-downloads",
            icon="tasks",
            url="/downloads",
            handler=this.props["toggler"]))
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
                                      {'menuItem': tr(this, "ui.mi-about-info", "Info"), },
                                      {'menuItem': tr(this, "ui.mi-about-plugins", "Plugins"), },
                                      {'menuItem': tr(this, "ui.mi-about-stats", "Statistics"), },
                                      {'menuItem': tr(this, "ui.mi-about-bug", "Report bug"), },
                                  ],
                                  menu=e(ui.Menu, secondary=True, pointing=True)))
                          ],
                          icon="info", position="right", handler=this.props["toggler"])
    items.append(about_item)
    items.append(
        MenuItem(
            "Trash",
            "ui.mi-trash",
            position="right",
            icon="trash",
            url="/trash",
            handler=this.props["toggler"]))
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

        item_children = (e(ui.Icon, js_name=menu_icon, className="left", size=icon_size),
                         tr(this, x.t_id, menu_name) if not icon else "",)

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

    el_args = {  'as':ui.Menu,
                 'animation':"overlay",
                 'width':nav_width,
                 'vertical':True,
                 'visible':this.props.toggled,
                 'icon':icon,
                 'defaultActiveIndex':3,
                 'size':"small",
                 'className':"window-height",
                 'inverted':True}

    if this.props.mobile:
        el_args['direction'] = "right"

    return e(ui.Sidebar, cnt_el, **el_args)

SideBar = createReactClass({
    'displayName': 'SideBar',

    'render': sidebar_nav_render
})
