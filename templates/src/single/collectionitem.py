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
js_undefined = location = localStorage = sessionStorage = None
__pragma__('noskip')


def collection_render():
    title = ""
    item_id = this.state.id
    fav = 0

    if this.state.data:
        title = this.state.data.title
        if not item_id:
            item_id = this.state.data.id
        if this.state.data.metatags.favorite:
            fav = 1

    return e(ui.Segment,
             e(ui.Card,
               e(ui.Dimmer.Dimmable,
                 h("div",
                   e(thumbitem.Thumbnail, item_id=item_id,
                    item_type=this.state.item_type, size_type=ImageSize.Medium),
                   e(ui.Rating, icon="heart", size="massive", className="card-item top left above-dimmer", rating=fav),
                   e(ui.Popup,
                     e(ui.List, [], selection=True, relaxed=True),
                       trigger=e(ui.Icon,
                                 js_name="ellipsis vertical",
                                 bordered=True,
                                 link=True,
                                 className="card-item bottom right above-dimmer",
                                 inverted=True),
                       hoverable=True,
                       on="click",
                       position="right center",
                     ),
                   className="card-content",
                   ),
                 dimmed=this.state.dimmer,
                 onMouseEnter=this.dimmer_show,
                 onMouseLeave=this.dimmer_hide,
                ),
                e(ui.Card.Content,
                                e(ui.Card.Header, title, className="text-ellipsis card-header"),
                                ),
                className=this.props.className,
                link=True),
             piled=True,
             stacked=True,
             className="no-padding-segment",
             )


Collection = createReactClass({
    'displayName': 'Collection',

    'getInitialState': lambda: {'id': None,
                                'data': None,
                                'gallery_count': 0,
                                'dimmer': False,
                                'galleries': [],
                                'item_type': ItemType.Collection},

    'dimmer_show': lambda: this.setState({'dimmer': True}),
    'dimmer_hide': lambda: this.setState({'dimmer': False}),

    'componentWillMount': lambda: this.setState({'data': this.props.data, 'id': 0}),

    'render': collection_render
})
