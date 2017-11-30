
__pragma__('alias', 'as_', 'as')
from src.react_utils import (h, e,
                             render,
                             React,
                             createReactClass,
                             NavLink)
from src.client import client
from src.state import state
from src.ui import ui
from src.i18n import tr
from src.utils import defined, is_same_machine

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
                             label=tr(props.tab, "", "Send path to first file in folder/archive"),
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
             menu=e(ui.Menu, secondary=True, pointing=True, stackable=True))


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