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
from src.utils import defined
from src.nav import MenuItem


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

    el_args = {'stackable': True, 'size': "small"}

    el = e(ui.Menu,
           *elements_left,
           *elements,
           *menu_contents,
           *elements_right,
           secondary=True,
           borderless=True,
           **el_args)

    return el

Menu = createReactClass({
    'displayName': 'Menu',

    'getInitialState': lambda: {'fixed': False},

    'render': menu_nav_render,

    'toggle_fixed': lambda: this.setState({'fixed': not this.state.fixed})
})
