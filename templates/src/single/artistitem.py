from src import utils
from src.react_utils import (e,
                             createReactClass)
from src.ui import ui
from src.client import ItemType
from src.propsviews import artistpropsview
from src.client import ItemType, client

from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

def update_metatags(mtags):
    if this.state.data:
        client.call_func("update_metatags", None, item_type=this.state.item_type,
                         item_id=this.state.data.id, metatags=mtags)
        d = this.props.data or this.state.data
        d.metatags = dict(d.metatags)
        d.metatags.update(mtags)
        d = utils.JSONCopy(d)
        this.setState({'data': d})

def item_favorite(e, d):
    e.preventDefault()
    if this.props.edit_mode:
        this.update_data(bool(d.rating), "metatags.favorite")
    else:
        this.update_metatags({'favorite': bool(d.rating)})

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

    return e(ui.Popup,
             e(artistpropsview.ArtistProps,
               data=data,
               tags=this.props.tags or this.state.tags,
               edit_mode=this.props.edit_mode,
               on_favorite=this.favorite),
             trigger=e(ui.Label,
                       e(ui.Icon, js_name="star") if fav else None,
                       e(ui.Icon, js_name="user circle outline"),
                       name,
                       e(ui.Icon, js_name="delete",
                         color=this.props.color,
                         link=True,
                         onClick=this.props.onRemove,
                         **{'data-id': data.id, 'data-name': name}) if this.props.edit_mode else None,
                       basic=True,
                       color="blue",
                       as_="a",
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

    'update_data': utils.update_data,

    'update_metatags': update_metatags,

    'favorite': item_favorite,

    'componentDidMount': lambda: this.get_tags() if not utils.defined(this.props.tags) else None,

    'render': artistlbl_render
}, pure=True)
