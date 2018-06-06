from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui
from src.client import (ItemType, ImageSize)
from src.single import thumbitem
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def grouping_render():
    title = ""
    item_id = this.state.id
    if this.state.data:
        title = this.state.data.js_name
        if not item_id:
            item_id = this.state.data.id

    artists = []
    for a in this.state.artists:
        if len(a.names) > 0:
            artists.append(a.names[0].js_name)
    artist_el = [h("span", x) for x in artists]

    return e(ui.Segment, e(ui.Card,
                           h("div",
                             e(thumbitem.Thumbnail, item_id=item_id,
                               item_type=this.state.item_type, size_type=ImageSize.Medium),
                               #e(ui.Label, e(ui.Icon, js_name="star half empty"), avg_rating, className="card-item bottom left", circular=True, size="large", color="orange"),
                               e(ui.Icon, js_name="ellipsis vertical", bordered=True,
                                 className="card-item bottom right", link=True, inverted=True),
                               e(ui.Label, e(ui.Icon, js_name="block layout"), len(
                                   this.state.galleries), className="card-item top right",),
                               className="card-content",
                             ),
                           e(ui.Popup,
                               trigger=e(ui.Card.Content,
                                         e(ui.Card.Header, title, className="text-ellipsis card-header"),
                                         e(ui.Card.Meta, *artist_el, className="text-ellipsis"),),
                               header=title,
                               content=h("div", *artist_el),
                               hideOnScroll=True,
                               position="bottom center"
                             ),
                           link=True),
             stacked=True,
             className="no-padding-segment",
             )


Grouping = createReactClass({
    'displayName': 'Grouping',

    'getInitialState': lambda: {'id': None,
                                'data': None,
                                'artists': [],
                                'galleries': [],
                                'item_type': ItemType.Grouping},

    'componentWillMount': lambda: this.setState({'data': this.props.data, 'id': 0}),

    'render': grouping_render
}, pure=True)
