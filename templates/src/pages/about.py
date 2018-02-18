

__pragma__('alias', 'as_', 'as')
from src.react_utils import (h, e,
                             render,
                             React,
                             createReactClass,
                             Link)
from src.client import client
from src.state import state
from src.ui import ui
from src.i18n import tr
from src.utils import defined, is_same_machine, get_version


__pragma__("tconv")


def about_info(props):
    top_items = []
    if is_same_machine():
        top_items.append(e(ui.Grid.Column, e(ui.Header, tr(props.that, "ui.de-about-same-machine", "You are currently connected from the same machine"),
                                             size="small", color="green", textAlign="center")))
    first_rows = []

    first_rows.append(e(ui.Table.Row,
                        e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-developer", "Developer"), as_="h5"), collapsing=True),
                        e(ui.Table.Cell, h("a", "Twiddly", href="https://github.com/Pewpews", target="_blank"))))
    first_rows.append(e(ui.Table.Row,
                        e(ui.Table.Cell, e(ui.Header, "Twitter", as_="h5"), collapsing=True),
                        e(ui.Table.Cell, h("a", "@pewspew", href="https://twitter.com/pewspew", target="_blank"))))

    second_rows = []
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-client-version", "Client version"), as_="h5"), collapsing=True),
                         e(ui.Table.Cell, e(ui.Label, get_version(), basic=True))))
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-server-version", "Server version"), as_="h5"), collapsing=True),
                         e(ui.Table.Cell, e(ui.Label, ".".join(props.version.core) if defined(props.version.core) else "", basic=True))))
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-database-version", "Database version"), as_="h5"), collapsing=True),
                         e(ui.Table.Cell, e(ui.Label, ".".join(props.version.db) if defined(props.version.db) else "", basic=True))))
    second_rows.append(e(ui.Table.Row,
                         e(ui.Table.Cell, e(ui.Header, tr(props.that, "ui.t-torrent-version", "Torrent Client version"), as_="h5"), collapsing=True),

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
                 e(ui.Button, e(ui.Icon, js_name="heart"), tr(props.that, "ui.b-support-patreon", "Support on patreon"),
                   as_="a", href="https://www.patreon.com/twiddly", target="_blank", color="orange", size="small"),
                 ),
               ),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Button, e(ui.Icon, js_name="repeat"), tr(props.that, "ui.b-restart", "Restart"),
                   color="blue", size="small", onClick=lambda: props.restart()),
                 e(ui.Button, e(ui.Icon, js_name="shutdown"), tr(props.that, "ui.b-shutdown", "Shutdown"),
                   color="red", size="small", onClick=lambda: props.shutdown()),
                 ),
               textAlign="right"
               ),
             divided="vertically",
             container=True,
             stackable=True,
             columns="equal"
             )


__pragma__("notconv")


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


def abouttab_check_update(data=None, error=None):
    if data is not None and not error:
        if data:
            state.new_update = True
        this.setState({"update_msg": data, 'update_checking': False})
    elif error:
        state.app.notif("Failed to check for updates", level="warning")
        this.setState({"update_checking": False})
    else:
        this.setState({"update_checking": True})
        client.call_func("check_update", this.check_update, push=True)


__pragma__("notconv")


def abouttab_render():
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
                               'content': tr(this, "ui.mi-about-plugins", "Plugins")}, },
                 {'menuItem': {'key': 'statistics', 'icon': 'bar chart',
                               'content': tr(this, "ui.mi-about-stats", "Statistics")}, },
                 {'menuItem': {'key': 'bug', 'icon': 'bug', 'content': tr(this, "ui.mi-about-bug", "Report bug")}, },
                 {'menuItem': {'key': 'trash', 'icon': 'trash', 'content': tr(this, "ui.mi-about-trash", "Trash")}, },
                 {'menuItem': {'key': 'license', 'icon': 'copyright', 'content': tr(this, "", "License")},
                     'render': lambda: e(about_license, that=this)},
             ],
             menu=e(ui.Menu, secondary=True, pointing=True, stackable=True))


AboutTab = createReactClass({
    'displayName': 'AboutTab',

    'getInitialState': lambda: {
        'version': {},
        'update_msg': {},
        'update_checking': False,
    },

    'get_version': abouttab_get_version,

    'restart': abouttab_restart,
    'shutdown': abouttab_shutdown,

    'check_update': abouttab_check_update,

    'componentDidMount': lambda: this.get_version(),

    'render': abouttab_render
})
