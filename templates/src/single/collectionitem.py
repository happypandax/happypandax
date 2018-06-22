from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
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


def collection_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


def collection_render():
    title = ""
    item_id = this.state.id
    fav = 0
    data = this.props.data or this.state.data

    if this.state.data:
        title = this.state.data.js_name
        if not item_id:
            item_id = this.state.data.id
        if this.state.data.metatags.favorite:
            fav = 1

    cls_name = "segment piled"
    if this.props.className:
        cls_name += ' ' + this.props.className

    collection_url = '/item/collection/' + str(item_id)

    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    thumb = e(thumbitem.Thumbnail,
              item_id=item_id,
              centered=True,
              blur=this.props.blur,
              item_type=this.state.item_type,
              size_type=this.props.size_type if this.props.size_type else ImageSize.Medium,
              )

    if link:
        thumb = e(Link, thumb, to={'pathname': collection_url,
                                   'state': {'collection': data},
                                   })

    return e(ui.Card,
             h("div",
               thumb,
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
                 hideOnScroll=True,
                 on="click",
                 position="right center",
                 ),
               className="card-content",
               ),
             e(ui.Card.Content,
               e(ui.Card.Header, title, className="text-ellipsis card-header"),
               ),
             centered=this.props.centered,
             # color="purple",
             className=cls_name,
             link=True)


Collection = createReactClass({
    'displayName': 'Collection',

    'getInitialState': lambda: {'id': None,
                                'data': None,
                                'gallery_count': 0,
                                'galleries': [],
                                'item_type': ItemType.Collection},

    'dimmer_show': lambda: this.setState({'dimmer': True}),
    'dimmer_hide': lambda: this.setState({'dimmer': False}),

    'componentWillMount': lambda: this.setState({'data': this.props.data, 'id': 0}),
    'componentDidUpdate': collection_on_update,

    'render': collection_render
}, pure=True)
