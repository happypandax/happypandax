from src.react_utils import (e,
                             createReactClass)
from src.ui import ui
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')
__pragma__('alias', 'js_input', 'input')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def genericitem_render():
    name = ""
    data = this.props.data or this.state.data
    if data:
        if this.props.preferred_name:
            if data.preferred_name:
                name = data.preferred_name.js_name
        else:
            name = data.js_name

    el_kwargs = {'active': this.props.active}
    el = e(this.props.as_ if this.props.as_ else ui.List.Item,
           this.props.icon if this.props.icon else None,
           e(ui.List.Content,
             e(ui.Header, name, size="tiny"),
             ),
           className=this.props.className,
           onClick=this.on_click,
           **el_kwargs if not this.props.as_ else None
           )
    return el


GenericItem = createReactClass({
    'displayName': 'GenericItem',

    'getInitialState': lambda: {
        'id': this.props.id,
        'data': this.props.data,
        'item_type': this.props.item_type,
    },

    'on_click': lambda e, d: all((this.props.onClick(e, this.props.data or this.state.data) if this.props.onClick else None,)),

    'render': genericitem_render
}, pure=True)
