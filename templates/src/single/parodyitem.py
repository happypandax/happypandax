from src.react_utils import (e,
                             createReactClass)
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

    lbl_args = {'content': name}
    return e(ui.Popup,
             e(parodypropsview.ParodyProps, data=data),
             trigger=e(ui.Label,
                       basic=True,
                       color="violet",
                       as_="a",
                       **lbl_args,
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

    'render': parodylbl_render
}, pure=True)
