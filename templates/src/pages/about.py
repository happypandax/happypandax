from src.react_utils import (h, e,
                             createReactClass)
from src import utils
from src.client import client, Command, PluginState
from src.state import state
from src.ui import ui
from src.i18n import tr
from src.utils import defined, is_same_machine, get_version
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


__pragma__("tconv")


def about_info(props):
    top_items = []
    if is_same_machine():
        top_items.append(e(ui.Grid.Column, e(ui.Header, tr(props.that, "ui.de-about-same-machine", "You are currently connected from the same machine"),
                                             size="small", color="green", textAlign="center")))
    first_rows = []

    first_rows.append(e(ui.Table.Row,
                        e(ui.Table.Cell, e(ui.Header, e(ui.Icon, js_name="github"), tr(
                            props.that, "ui.t-developer", "Developer"), as_="h5"), collapsing=True),
                        e(ui.Table.Cell, h("a", "Twiddly", href="https://github.com/Pewpews", target="_blank"))))
    first_rows.append(e(ui.Table.Row,
                        e(ui.Table.Cell, e(ui.Header, e(ui.Icon, js_name="twitter"), "Twitter", as_="h5"), collapsing=True),
                        e(ui.Table.Cell, h("a", "@pewspew", href="https://twitter.com/pewspew", target="_blank"))))

    second_rows = []
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-client-version",
                                                          "Client version"), as_="h5"), collapsing=True),
                         e(ui.Table.Cell, e(ui.Label, get_version(), basic=True))))
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-server-version",
                                                          "Server version"), as_="h5"), collapsing=True),
                         e(ui.Table.Cell, e(ui.Label, ".".join(props.version.core) if defined(props.version.core) else "", basic=True))))
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-database-version",
                                                          "Database version"), as_="h5"), collapsing=True),
                         e(ui.Table.Cell, e(ui.Label, ".".join(props.version.db) if defined(props.version.db) else "", basic=True))))
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-torrent-version",
                                                          "Torrent Client version"), as_="h5"), collapsing=True),

                         e(ui.Table.Cell, e(ui.Label, ".".join(props.version.torrent) if defined(props.version.torrent) else "", basic=True))))

    if props.update_checking:
        upd_button = e(ui.Button, e(ui.Icon, js_name="refresh", loading=True), tr(props.that, "ui.b-checking-update", "Checking for new update"),
                       onClick=lambda: props.check_update(), color="orange", size="small")
    elif props.update_msg or state.new_update:
        upd_button = e(ui.Button, e(ui.Icon, js_name="checkmark"), tr(props.that, "ui.b-new-update", "A new update is available!"),
                       onClick=lambda: props.check_update(), color="green", size="small")
    else:
        upd_button = e(ui.Button, e(ui.Icon, js_name="refresh"), tr(props.that, "ui.b-check-update", "Check for updates"),
                       onClick=lambda: props.check_update(), size="small")

    return e(ui.Grid,
             e(ui.Grid.Row, *top_items),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Table,
                     e(ui.Table.Body,
                       *first_rows
                       ),
                     basic="very",
                     size="small"
                   )
                 )
               ),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Table,
                     e(ui.Table.Body,
                       *second_rows
                       ),
                     basic="very",
                     size="small"
                   )
                 )
               ),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 upd_button,
                 e(ui.Button, e(ui.Icon, js_name="github"), tr(props.that, "ui.b-github-repo", "Github Repo"),
                   as_="a", href="https://github.com/happypandax", target="_blank", size="small"),
                 e(ui.Button, e(ui.Icon, js_name="heart"), tr(props.that, "ui.b-support-patreon", "Support on Patreon"),
                   as_="a", href="https://www.patreon.com/twiddly", target="_blank", color="orange", size="small"),
                 e(ui.Button, e(ui.Icon, js_name="repeat"), tr(props.that, "ui.b-reset", "Reset"), size="small", floated="right",
                   onClick=lambda: all((utils.storage.clear(True), utils.session_storage.clear(True)))),
                 ),
               ),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Button, e(ui.Icon, js_name="repeat"), tr(props.that, "ui.b-restart", "Restart"),
                   color="blue", size="tiny", onClick=lambda: props.restart()),
                 e(ui.Button, e(ui.Icon, js_name="shutdown"), tr(props.that, "ui.b-shutdown", "Shutdown"),
                   color="red", size="tiny", onClick=lambda: props.shutdown()),
                 ),
               textAlign="right",
               ),
             divided="vertically",
             container=True,
             stackable=True,
             columns="equal"
             )


__pragma__("notconv")


def about_plugins(props):

    plugin_els = []
    for p in props.plugins:
        plugin_els.append(
            e(ui.Card,
              e(ui.Card.Content,
                e(ui.Card.Header, p.js_name, e(ui.Label, p.version, size="small", className="right")),
                e(ui.Card.Meta,
                    e(ui.Label, p.shortname, size="tiny", basic=True),
                    e(ui.Label, p.id, size="tiny", basic=True),
                  ),
                e(ui.Card.Description, p.description),
                e(ui.Divider, hidden=True),
                e(ui.Label, p.author, size="small", color="blue"),
                *([e(ui.Label, tr(props.that, "ui.t-website", "Website"), size="small",
                     basic=True, as_="a", href=p.website, target="_blank")] if p.website else []),
                *([e(ui.Label, p.status, size="small", basic=True, color="red", className="right")] if p.status else []),
                e(ui.Divider),
                h("div",
                    e(ui.Button,
                      tr(props.that, "ui.b-install", "Install") if p.state == PluginState.Registered else
                      tr(props.that, "ui.b-enabled", "Enabled") if p.state == PluginState.Enabled else
                      tr(props.that, "ui.b-enable", "Enable") if p.state == PluginState.Disabled else
                      tr(props.that, "ui.b-not-enabled", "Not enabled"),
                      disabled=False if p.state in (PluginState.Registered, PluginState.Disabled) else True,
                      value=p.id,
                      onClick=lambda ev, da: all((client.call_func("install_plugin", plugin_id=da.value),
                                                  props.get_plugins())),
                      color="green", basic=False if p.state == PluginState.Enabled else True,
                      size="small"),
                    e(ui.Button,
                      tr(props.that, "ui.b-disable", "Disable") if p.state not in (PluginState.Disabled, PluginState.Failed, PluginState.Unloaded) else
                      tr(props.that, "ui.b-disabled", "Disabled") if p.state == PluginState.Disabled else
                      tr(props.that, "ui.b-not-loaded", "Not loaded") if p.state == PluginState.Unloaded else
                      tr(props.that, "ui.b-failed", "Failed"),
                      disabled=True if p.state in (
                          PluginState.Disabled,
                          PluginState.Failed,
                          PluginState.Unloaded) else False,
                        value=p.id,
                      onClick=lambda ev, da: all((client.call_func("disable_plugin", plugin_id=da.value),
                                                  props.get_plugins())),
                      color="black", basic=False if p.state == PluginState.Disabled else True,
                      size="small"),
                    e(ui.Button,
                      tr(props.that, "ui.b-remove", "Remove"),
                      value=p.id,
                      onClick=lambda ev, da: all((client.call_func("remove_plugin", plugin_id=da.value),
                                                  props.get_plugins())),
                      color="red", basic=True, size="small"),
                    className="ui three buttons tiny"
                  ),
                ),
                className="default-card",
                fluid=True,
              )
        )

    return e(ui.Card.Group,
             *plugin_els,
             stackable=True,
             doubling=True,
             )


def about_trash(props):

    plugin_els = []

    return e(ui.Card.Group,
             *plugin_els,
             stackable=True,
             doubling=True,
             )


def about_license(props):

    return e(ui.Grid,
             e(ui.Grid.Row,),
             e(ui.Grid.Row,
               h("pre",
                 """
HappyPanda X is a cross platform manga/doujinshi manager with namespace & tag support;
Copyright (C) 2017 Twiddly

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
             """)),
             divided="vertically",
             container=True,
             )


def about_changelog(props):
    els = []

    if props.changelog.version:
        els.append(e(ui.Grid.Row, e(ui.Header, props.changelog['version'])))

    if props.changelog.changes:
        els.append(e(ui.Grid.Row, dangerouslySetInnerHTML={'__html': utils.marked(props.changelog.changes)}))

    return e(ui.Grid,
             *els,
             divided="vertically",
             container=True,
             )


def abouttab_get_plugins(data=None, error=None):
    if data is not None and not error:
        this.setState({"plugins": data})
    elif error:
        state.app.notif("Failed to retrieve plugins", level="warning")
    else:
        client.call_func("list_plugins", this.get_plugins)


def abouttab_get_version(data=None, error=None):
    if data is not None and not error:
        this.setState({"version": data})
    elif error:
        state.app.notif("Failed to retrieve version info", level="warning")
    else:
        client.call_func("get_version", this.get_version)


def abouttab_restart(data=None, error=None):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to restart", level="warning")
    else:
        client.call_func("restart_application", this.restart)


def abouttab_shutdown(data=None, error=None):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to shutdown", level="warning")
    else:
        client.call_func("shutdown_application", this.shutdown)


__pragma__("tconv")


def abouttab_check_update_value(cmd):
    cmd_data = cmd.get_value()
    if cmd_data:
        state.new_update = True
    this.setState({"update_msg": cmd_data, 'update_checking': False})


def abouttab_check_update(data=None, error=None):
    if data is not None and not error:
        cmd = Command(data)
        cmd.poll_until_complete(3000, callback=this.check_update_value)
    elif error:
        state.app.notif("Failed to check for updates", level="warning")
        this.setState({"update_checking": False})
    else:
        this.setState({"update_checking": True})
        client.call_func("check_update", this.check_update, push=True)


def abouttab_get_changelog(data=None, error=None):
    if data is not None and not error:
        this.setState({"changelog": data})
    elif error:
        state.app.notif("Failed to get changelog", level="warning")
    else:
        client.call_func("get_changelog", this.get_changelog)


__pragma__("notconv")


def abouttab_render():
    get_plugins = this.get_plugins
    changelog = this.state.changelog
    plugins = this.state.plugins
    version = this.state.version
    update_msg = this.state.update_msg
    check_update = this.check_update
    update_checking = this.state.update_checking
    restart = this.restart
    shutdown = this.shutdown
    return e(ui.Tab,
             panes=[
                 {'menuItem': {'key': 'info', 'icon': 'info circle', 'content': tr(this, "ui.mi-about-info", "Info")},
                  'render': lambda: e(about_info, that=this,
                                      version=version,
                                      update_msg=update_msg,
                                      update_checking=update_checking,
                                      check_update=check_update,
                                      restart=restart,
                                      shutdown=shutdown)},
                 {'menuItem': {'key': 'plugins', 'icon': 'cubes',
                               'content': tr(this, "ui.mi-about-plugins", "Plugins")},
                     'render': lambda: e(about_plugins, that=this,
                                         plugins=plugins,
                                         get_plugins=get_plugins,
                                         )},
                 {'menuItem': {'key': 'statistics', 'icon': 'bar chart',
                               'content': tr(this, "ui.mi-about-stats", "Statistics")}, },
                 {'menuItem': {'key': 'bug', 'icon': 'bug', 'content': tr(this, "ui.mi-about-bug", "Report bug")}, },
                 {'menuItem': {'key': 'trash', 'icon': 'trash', 'content': tr(this, "ui.mi-about-trash", "Trash")},
                     'render': lambda: e(about_trash, that=this,)},
                 {'menuItem': {'key': 'changelog', 'icon': 'announcement', 'content': tr(this, "ui.mi-about-changelog", "Changelog")},
                     'render': lambda: e(about_changelog, that=this, changelog=changelog)},
                 {'menuItem': {'key': 'license', 'icon': 'copyright', 'content': tr(this, "ui.mi-about-license", "License")},
                     'render': lambda: e(about_license, that=this)},
             ],
             menu=e(ui.Menu, secondary=True, pointing=True, stackable=True))


AboutTab = createReactClass({
    'displayName': 'AboutTab',

    'getInitialState': lambda: {
        'plugins': [],
        'changelog': {'changes': '', 'version': ''},
        'version': {},
        'update_msg': {},
        'update_checking': False,
    },

    'get_version': abouttab_get_version,
    'get_plugins': abouttab_get_plugins,
    'get_changelog': abouttab_get_changelog,

    'restart': abouttab_restart,
    'shutdown': abouttab_shutdown,

    'check_update_value': abouttab_check_update_value,
    'check_update': abouttab_check_update,

    'componentDidMount': lambda: all((this.get_version(),
                                      this.get_plugins(),
                                      this.get_changelog(),
                                      )),

    'render': abouttab_render
}, pure=True)
