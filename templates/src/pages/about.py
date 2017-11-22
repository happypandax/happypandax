

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
from src.utils import defined, is_same_machine

def about_info(props):
    top_items = []
    if is_same_machine():
        top_items.append(e(ui.Grid.Column, e(ui.Header, tr(props.that, "", "You are currently connected from the same machine"),
                                             size="small", color="green", textAlign="center")))

    return e(ui.Grid,
             e(ui.Grid.Row, *top_items ),
             e(ui.Grid.Row,),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Button, e(ui.Icon, js_name="refresh"), tr(props.that, "", "Check for updates")),
                 e(ui.Button, e(ui.Icon, js_name="home"), tr(props.that, "", "Visit homepage"),
                   as_="a", href="https://github.com/happypandax", target="_blank"),
                 #e(ui.Button, e(ui.Icon, js_name="heart"), tr(props.that, "", "Support on patreon"),
                 #  as_="a", href="https://github.com/happypandax", target="_blank"),
                 ),

               ),
             divided=True,
             container=True,
             stackable=True,
             columns="equal"
             )

def abouttab_render():

    return e(ui.Tab,
             panes=[
                 {'menuItem': { 'key':'info', 'icon':'info circle', 'content': tr(this, "ui.mi-about-info", "Info")},
                  'render': lambda: e(about_info, that=this)},
                {'menuItem': { 'key':'plugins', 'icon':'cubes', 'content': tr(this, "ui.mi-about-plugins", "Plugins")}, },
                {'menuItem': { 'key':'statistics', 'icon':'bar chart', 'content': tr(this, "ui.mi-about-stats", "Statistics")}, },
                {'menuItem': { 'key': 'bug', 'icon':'bug', 'content': tr(this, "ui.mi-about-bug", "Report bug") }, },
                {'menuItem': { 'key':'trash', 'icon':'trash', 'content': tr(this, "ui.mi-about-trash", "Trash") }, },
             ],
             menu=e(ui.Menu, secondary=True, pointing=True, stackable=True))


AboutTab = createReactClass({
    'displayName': 'AboutTab',

    'getInitialState': lambda: {'config': {}, 'refresh': False, 'u_config': {}},

    #'componentDidMount': lambda: this.get_config(),

    'render': abouttab_render
})