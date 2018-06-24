from src import utils
from src.react_utils import (e,
                             createReactClass)
from src.ui import ui
from src.client import ItemType
from src.propsviews import artistpropsview
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def artistlbl_render():
    name = ""
    fav = 0
    data = this.props.data or this.state.data
    if data:
        if data.preferred_name:
            name = data.preferred_name.js_name
        if data.metatags:
            if data.metatags.favorite:
                fav = 1

    lbl_args = {'content': name}
    if fav:
        lbl_args['icon'] = "star"
    else:
        lbl_args['icon'] = "user circle outline"
    return e(ui.Popup,
             e(artistpropsview.ArtistProps, data=data, tags=this.props.tags or this.state.tags),
             trigger=e(ui.Label,
                       basic=True,
                       color="blue",
                       as_="a",
                       **lbl_args,
                       ),
             hoverable=True,
             hideOnScroll=True,
             wide="very",
             on="click",
             position="top center"
             )


__pragma__("notconv")

ArtistLabel = createReactClass({
    'displayName': 'ArtistLabel',

    'getInitialState': lambda: {
        'id': this.props.id,
        'data': this.props.data,
        'tags': this.props.tags,
        'item_type': ItemType.Artist,
    },

    'get_tags': artistpropsview.get_tags,

    'componentDidMount': lambda: this.get_tags() if not utils.defined(this.props.tags) else None,

    'render': artistlbl_render
}, pure=True)
