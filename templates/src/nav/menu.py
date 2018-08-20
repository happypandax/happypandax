from src.react_utils import (e,
                             createReactClass)
from src.ui import ui
from src.utils import defined
from src.nav import MenuItem
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Object = Date = None
__pragma__('noskip')


def connect_render():
    ic_kwargs = {'size': "large"}
    if this.state.loading:
        ic_kwargs['name'] = "circle notch"
        ic_kwargs['loading'] = True
        ic_kwargs['color'] = "orange"
        del ic_kwargs['size']
    else:
        if this.state.connected:
            ic_kwargs['name'] = "circle notch"
            ic_kwargs['color'] = "green"
        else:
            ic_kwargs['name'] = "circle notch"
            ic_kwargs['color'] = "red"

    return e(ui.Menu.Item,
             icon=e(ui.Icon, **ic_kwargs),
             )


Connect = createReactClass({
    'displayName': 'Connect',

    'getInitialState': lambda: {'connected': True,
                                'loading': False},

    'render': connect_render,

}, pure=False)


def menu_nav_render():
    icon_size = "large"

    items = []
    items.append(MenuItem("", position="left", header=True, handler=this.props["toggler"],
                          content=e(ui.Icon, className="hpx-standard huge")))

    elements = []
    elements_left = []
    elements_right = []

    # elements_right.append(e(Connect))

    for n, x in enumerate(items, 1):
        menu_name = x.name
        menu_icon = x.icon

        if x.position == "right":
            container = elements_right
        elif x.position == "left":
            container = elements_left
        else:
            container = elements

        children = []
        for c in x.children:
            children.append(e(ui.Dropdown.Item, c.name))
        content = menu_name if x.content is None else x.content

        icon_el = []
        if menu_icon:
            icon_el.append(e(ui.Icon, js_name=menu_icon, size=icon_size))

        container.append(e(ui.Menu.Item,
                           *icon_el,
                           content,
                           js_name=menu_name if x.content is None else None,
                           header=x.header,
                           onClick=x.handler,
                           index=n,
                           icon=not menu_name,
                           )
                         )
    menu_contents = this.props.contents
    if not isinstance(menu_contents, list):
        menu_contents = [menu_contents]

    if defined(this.props.menu_args):
        menu_args = this.props.menu_args
    else:
        menu_args = {}

    el = e(ui.Menu,
           *elements_left,
           *elements,
           *menu_contents,
           *elements_right,
           secondary=False if this.props.fixed else True,
           borderless=True,
           stackable=True,
           fixed="top" if this.props.fixed is True else this.props.fixed if this.props.fixed else js_undefined,
           size="tiny",
           **menu_args
           )

    return el


Menu = createReactClass({
    'displayName': 'Menu',

    'getInitialState': lambda: {'fixed': False},

    'render': menu_nav_render,

    'toggle_fixed': lambda: this.setState({'fixed': not this.state.fixed})
}, pure=False)
