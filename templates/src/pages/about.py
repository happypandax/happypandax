

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

def about_info(props):
    top_items = []
    if is_same_machine():
        top_items.append(e(ui.Grid.Column, e(ui.Header, tr(props.that, "", "You are currently connected from the same machine"),
                                             size="small", color="green", textAlign="center")))
    first_rows = []

    first_rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(props.that, "", "Developer"), as_="h5"), collapsing=True),
                  e(ui.Table.Cell, h("a", "Twiddly", href="https://github.com/Pewpews"))))
    first_rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(props.that, "", "Twitter"), as_="h5"), collapsing=True),
                  e(ui.Table.Cell, h("a", "@pewspew", href="https://twitter.com/pewspew"))))

    second_rows = []
    second_rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(props.that, "", "Client version"), as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, get_version(), basic=True))))
    second_rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(props.that, "", "Server version"), as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, ".".join(props.version.core) if defined(props.version.core) else "", basic=True))))
    second_rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(props.that, "", "Database version"), as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, ".".join(props.version.db) if defined(props.version.db) else "", basic=True))))
    second_rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(props.that, "", "Torrent Client version"), as_="h5"), collapsing=True),

                  e(ui.Table.Cell, e(ui.Label, ".".join(props.version.torrent) if defined(props.version.torrent) else "", basic=True))))
    return e(ui.Grid,
             e(ui.Grid.Row, *top_items ),
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
                 e(ui.Button, e(ui.Icon, js_name="refresh"), tr(props.that, "", "Check for updates")),
                 e(ui.Button, e(ui.Icon, js_name="home"), tr(props.that, "", "Visit homepage"),
                   as_="a", href="https://github.com/happypandax", target="_blank"),
                 #e(ui.Button, e(ui.Icon, js_name="heart"), tr(props.that, "", "Support on patreon"),
                 #  as_="a", href="https://github.com/happypandax", target="_blank"),
                 ),

               ),
             divided="vertically",
             container=True,
             stackable=True,
             columns="equal"
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


def abouttab_get_version(data=None, error=None):
    if data is not None and not error:
        this.setState({"version": data})
    elif error:
        state.app.notif("Failed to retrieve version info", level="warning")
    else:
        client.call_func("get_version", this.get_version)

def abouttab_render():
    version = this.state.version
    return e(ui.Tab,
             panes=[
                 {'menuItem': { 'key':'info', 'icon':'info circle', 'content': tr(this, "ui.mi-about-info", "Info")},
                  'render': lambda: e(about_info, that=this, version=version)},
                {'menuItem': { 'key':'plugins', 'icon':'cubes', 'content': tr(this, "ui.mi-about-plugins", "Plugins")}, },
                {'menuItem': { 'key':'statistics', 'icon':'bar chart', 'content': tr(this, "ui.mi-about-stats", "Statistics")}, },
                {'menuItem': { 'key': 'bug', 'icon':'bug', 'content': tr(this, "ui.mi-about-bug", "Report bug") }, },
                {'menuItem': { 'key':'trash', 'icon':'trash', 'content': tr(this, "ui.mi-about-trash", "Trash") }, },
                {'menuItem': { 'key':'license', 'icon':'copyright', 'content': tr(this, "", "License") },
                  'render': lambda: e(about_license, that=this)},
             ],
             menu=e(ui.Menu, secondary=True, pointing=True, stackable=True))


AboutTab = createReactClass({
    'displayName': 'AboutTab',

    'getInitialState': lambda: {
        'version': {},
        },

    'get_version': abouttab_get_version,

    'componentDidMount': lambda: this.get_version(),

    'render': abouttab_render
})