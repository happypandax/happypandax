
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

disabled_machine_msg = lambda props: e(ui.Message, tr(props.tab, "", "Disabled because this client is connecting from a different device"), color="yellow")

def pref_general(props):
    cfg = props.cfg
    u_cfg = props.u_cfg
    items = []
    if defined(cfg.gallery):

        if defined(cfg.gallery.external_image_viewer):
            items.append(e(ui.Header, tr(props.tab, "", "External Viewer"), size="small", dividing=True))

            if not is_same_machine():
                ext_viewer.append(disabled_machine_msg(props))


            items.append(e(ui.Form.Group,
                           e(ui.Form.Input,
                           width=10,
                           label=tr(props.tab, "", "External Image Viewer"),
                           placeholder=tr(props.tab, "", "path/to/executable"),
                           defaultValue=cfg.gallery.external_image_viewer,
                           onChange=lambda e: props.upd("gallery.external_image_viewer", e.target.value),
                           disabled=not is_same_machine(),
                           ),
                           e(ui.Form.Input,
                           width=6,
                           label=tr(props.tab, "", "External Image Viewer Arguments"),
                           placeholder=tr(props.tab, "", "example: -a -X --force"),
                           defaultValue=cfg.gallery.external_image_viewer_args,
                           onChange=lambda e: props.upd("gallery.external_image_viewer_args", e.target.value),
                           disabled=not is_same_machine(),
                           )
                           ))

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

    if defined(cfg.search):
        items.append(e(ui.Header, tr(props.tab, "", "Search"), size="small", dividing=True))

        if defined(cfg.search.regex):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Allow regex in search filters"),
                             defaultChecked=cfg.search.regex,
                             onChange=lambda e, d: props.upd("search.regex", d.checked),
                             ))
                         )

        if defined(cfg.search.case_sensitive):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Search filter is case sensitive"),
                             defaultChecked=cfg.search.case_sensitive,
                             onChange=lambda e, d: props.upd("search.case_sensitive", d.checked),
                             ))
                         )


        if defined(cfg.search.match_whole_words):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Match terms exact"),
                             defaultChecked=cfg.search.match_whole_words,
                             onChange=lambda e, d: props.upd("search.match_whole_words", d.checked),
                             ))
                         )

        if defined(cfg.search.match_all_terms):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Match only items that has all terms"),
                             defaultChecked=cfg.search.match_all_terms,
                             onChange=lambda e, d: props.upd("search.match_all_terms", d.checked),
                             ))
                         )

        if defined(cfg.search.descendants):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Also match on children"),
                             defaultChecked=cfg.search.descendants,
                             onChange=lambda e, d: props.upd("search.descendants", d.checked),
                             ))
                         )


    if defined(cfg.core):

        if defined(cfg.core.check_new_releases):
            items.append(e(ui.Header, tr(props.tab, "", "Updates"), size="small", dividing=True))
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Regularly check for new releases"),
                             defaultChecked=cfg.core.check_new_releases,
                             onChange=lambda e, d: props.upd("core.check_new_releases", d.checked),
                             ))
                         )

        if defined(cfg.core.check_release_interval):
            items.append(e(ui.Form.Field,
                           h("label", tr(props.tab, "", "Interval in minutes between checking for a new release, set 0 to only check once every startup")),
                           e(ui.Input,
                             width=4,
                             js_type="number",
                             defaultValue=cfg.core.check_release_interval,
                             onChange=lambda e, d: props.upd("core.check_release_interval", int(e.target.value)),
                             ))
                         )

        if defined(cfg.core.allow_beta_releases):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Allow downloading beta releases"),
                             defaultChecked=cfg.core.allow_beta_releases,
                             onChange=lambda e, d: props.upd("core.allow_beta_releases", d.checked),
                             ))
                         )

        if defined(cfg.core.allow_alpha_releases):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Allow downloading alpha releases"),
                             defaultChecked=cfg.core.allow_alpha_releases,
                             onChange=lambda e, d: props.upd("core.allow_alpha_releases", d.checked),
                             ))
                         )

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
        items.append(e(ui.Message, tr(props.tab, "",
                                      "These changes require a server restart."), info=True))

        items.append(e(ui.Header, tr(props.tab, "", "Server"), size="small", dividing=True))

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

        if defined(cfg.server.host) and defined(cfg.server.port):
            items.append(e(ui.Form.Group,
                           e(ui.Form.Input,
                             width=10,
                             label=tr(props.tab, "", "Server Host"),
                             placeholder="localhost",
                             defaultValue=cfg.server.host,
                             onChange=lambda e: props.upd("server.host", e.target.value)
                             ),
                           e(ui.Form.Input,
                             width=4,
                             label=tr(props.tab, "", "Server Port"),
                             placeholder="7007",
                             defaultValue=cfg.server.port,
                             onChange=lambda e: props.upd("server.port", int(e.target.value))
                             ),
                           )
                         )

        items.append(e(ui.Header, tr(props.tab, "", "Web Client"), size="small", dividing=True))

        if defined(cfg.server.host_web) and defined(cfg.server.port_web):
            items.append(e(ui.Form.Group,
                           e(ui.Form.Input,
                             width=10,
                             label=tr(props.tab, "", "Web Client Host"),
                             placeholder="",
                             defaultValue=cfg.server.host_web,
                             onChange=lambda e: props.upd("server.host_web", e.target.value)
                             ),
                           e(ui.Form.Input,
                             width=4,
                             label=tr(props.tab, "", "Web Client Port"),
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

def pref_advanced(props):
    cfg = props.cfg
    u_cfg = props.u_cfg
    items = []
    if defined(cfg.core):
        if defined(cfg.core.debug):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Run in debug mode"),
                             defaultChecked=cfg.core.debug,
                             onChange=lambda e, d: props.upd("core.debug", d.checked),
                             ))
                         )

        if defined(cfg.core.report_critical_errors):
            items.append(e(ui.Form.Field,
                           e(ui.Checkbox,
                             toggle=True,
                             label=tr(props.tab, "", "Send occurring critical errors to me (creator) so I can fix them faster (contains no sensitive information)"),
                             defaultChecked=cfg.core.report_critical_errors,
                             onChange=lambda e, d: props.upd("core.report_critical_errors", d.checked),
                             ))
                         )

        if defined(cfg.core.unrar_tool_path):
            items.append(e(ui.Form.Group,
                           e(ui.Form.Input,
                             width=16,
                             label=tr(props.tab, "", "Path to unrar tool"),
                             placeholder=tr(props.tab, "", "unrar"),
                             defaultValue=cfg.core.unrar_tool_path,
                             onChange=lambda e: props.upd("core.unrar_tool_path", e.target.value)
                             ))
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
                 {'menuItem': tr(this, "ui.mi-pref-server", "Server"),
                  'render': lambda: el(pref_server)},
                 {'menuItem': tr(this, "ui.mi-pref-advanced", "Advanced"),
                  'render': lambda: el(pref_advanced)},
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
