from src.react_utils import (e,
                             createReactClass)
from src import utils
from src.ui import ui
from src.client import ItemType
from src.propsviews import parodypropsview
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def parodylbl_render():
    name = ""
    data = this.props.data or this.state.data
    if data:
        if data.preferred_name:
            name = data.preferred_name.js_name
        elif data.names and len(data.names):
            name = data.names[0]

    return e(ui.Popup,
             e(parodypropsview.ParodyProps, data=data),
             trigger=e(ui.Label,
                       name,
                       e(ui.Icon, js_name="delete",
                         color=this.props.color,
                         link=True,
                         onClick=this.props.onRemove,
                         **{'data-id': data.id, 'data-name': name}) if this.props.edit_mode or this.props.showRemove else None,
                       basic=True,
                       color="violet",
                       as_="a",
                       ),
             hoverable=True,
             wide="very",
             on="click",
             hideOnScroll=True,
             position="top center"
             )


__pragma__("notconv")

ParodyLabel = createReactClass({
    'displayName': 'ParodyLabel',

    'getInitialState': lambda: {
        'id': this.props.id,
        'data': this.props.data,
        'item_type': ItemType.Parody,
    },

    'update_data': utils.update_data,

    'render': parodylbl_render
}, pure=True)


def parodyitem_render():
    name = ""
    data = this.props.data or this.state.data
    if data:
        if data.preferred_name:
            name = data.preferred_name.js_name

    el_kwargs = {'active': this.props.active}
    el = e(this.props.as_ if this.props.as_ else ui.List.Item,
           #e(ui.Icon, js_name="user circle", size="big", disabled=True),
           e(ui.List.Content,
             e(ui.Header, name, size="tiny"),
             ),
           className=this.props.className,
           onClick=this.on_click,
           **el_kwargs if not this.props.as_ else None
           )

    if not this.props.selection:
        el = e(ui.Popup,
               e(parodypropsview.ParodyProps, data=data),
               trigger=el,
               hoverable=True,
               hideOnScroll=True,
               wide="very",
               on="click",
               position="top center"
               )

    return el


ParodyItem = createReactClass({
    'displayName': 'ParodyItem',

    'getInitialState': lambda: {
        'id': this.props.id,
        'data': this.props.data,
        'item_type': ItemType.Parody,
    },

    'update_data': utils.update_data,

    'on_click': lambda e, d: all((this.props.onClick(e, this.props.data or this.state.data) if this.props.onClick else None,)),

    'render': parodyitem_render
}, pure=True)
