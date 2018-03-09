import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
from src.ui import ui
from src.client import (ItemType, ImageSize, client)
from src.state import state
from src.single import thumbitem
from src import utils
from src.views import tagview
from src.propsviews import gallerypropsview
from src.i18n import tr
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def on_tags(data):
    this.setState({'tags': data})


def gallery_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


__pragma__("tconv")


def open_external(e, d):
    e.preventDefault()
    if this.state.data:
        client.call_func("open_gallery", None, item_id=this.state.data.id, item_type=this.state.item_type)


__pragma__("notconv")


def gallery_render():
    fav = 0
    title = ""
    rating = 0
    urls = []
    artists = []
    artist_names = []
    item_id = this.state.id
    inbox = False
    data = this.props.data or this.state.data

    if this.state.data:
        read_count = this.state.data.times_read
        rating = this.state.data.rating
        title = this.state.data.titles[0].js_name
        inbox = this.state.data.metatags.inbox

        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id

        for a in this.state.data.artists:
            if len(a.names) > 0:
                artist_names.append(a.names[0].js_name)
        artists = this.state.data.artists

        for u in this.state.data.urls:
            urls.append(u.js_name)

    add_cls = this.props.className or ""
    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    read_button_args = {}
    if this.props.external_viewer:
        read_button_args['onClick'] = this.open_external
    else:
        read_button_args['as'] = Link
        read_button_args['to'] = utils.build_url("/item/page", {'gid': item_id}, keep_query=False)

    thumb = e(thumbitem.Thumbnail,
              item_id=item_id,
              centered=True,
              item_type=this.state.item_type,
              size_type=ImageSize.Medium,
              size=this.props.size,
              dimmer=e(ui.Dimmer,
                       active=this.state.dimmer,
                       content=e(ui.Responsive,
                                 e(ui.List,
                                   e(ui.List.Item, e(ui.Button, tr(this, "ui.b-read", "Read"),
                                                     primary=True, size="tiny", **read_button_args)),
                                   e(ui.List.Item, e(ui.Button, e(ui.Icon, js_name="bookmark outline"), tr(this, "ui.b-save-later", "Save for later"), size="tiny") if not inbox else
                                     e(ui.Button, e(ui.Icon, js_name="grid layout"), tr(this, "ui.b-send-library", "Send to library"), color="green", size="tiny")),
                                   ),
                                 minWidth=1000,
                                 ),
                       inverted=True),
              )
    if link:
        thumb = e(Link, thumb, to={'pathname': '/item/gallery',
                                   'search': utils.query_to_string({'id': item_id})})

    menu_options = []
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-read", "Read"), **read_button_args))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-save-later", "Save for later"), icon="bookmark outline"))
    if inbox:
        menu_options.append(e(ui.List.Item, content=tr(
            this, "ui.b-send-library", "Send to library"), icon="grid layout"))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-add-to-filter", "Add to filter"), icon="filter"))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-add-to-collection",
                                                   "Add to collection"), icon="plus square outline"))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-add-to-series", "Add to series"), icon="add square"))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-send-trash", "Send to Trash"), icon="trash"))

    return e(ui.Card,
             e(ui.Dimmer.Dimmable,
                 h("div",
                   thumb,
                   e(ui.Rating, icon="heart", size="massive", className="card-item top left above-dimmer", rating=fav),
                   e(ui.Popup,
                     e(ui.Rating, icon="star", defaultRating=rating, maxRating=10, clearable=True, className=""),
                     trigger=e(
                         ui.Label,
                         rating,
                         className="card-item bottom left above-dimmer",
                         size="large",
                         color="yellow",
                         as_="a"),
                       hoverable=True,
                       on="click",
                       hideOnScroll=True,
                       position="left center",
                     ),
                   e(ui.Popup,
                     e(ui.List, *menu_options, selection=True, relaxed=True),
                       trigger=e(ui.Icon,
                                 js_name="ellipsis vertical",
                                 bordered=True,
                                 link=True,
                                 className="card-item bottom right above-dimmer",
                                 inverted=True),
                       hoverable=True,
                       on="click",
                       hideOnScroll=True,
                       position="right center",
                     ),
                   className="card-content",
                   ),
                 dimmed=this.state.dimmer,
                 onMouseEnter=this.dimmer_show,
                 onMouseLeave=this.dimmer_hide,
               ),
             e(ui.Popup,
               trigger=e(ui.Card.Content,
                         e(ui.Card.Header, title, className="text-ellipsis card-header"),
                         e(ui.Card.Meta, *[h("span", x) for x in artist_names], className="text-ellipsis"),
                         ),
               content=e(gallerypropsview.GalleryProps, data=data, tags=this.state.tags, on_tags=this.on_tags),
               hideOnScroll=True,
               hoverable=True,
               position="bottom center",
               wide="very",
               on="click"
               ),
             centered=this.props.centered,
             className=add_cls,
             link=True)


Gallery = createReactClass({
    'displayName': 'Gallery',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                'tags': this.props.tags,
                                'dimmer': False,
                                },
    'open_external': open_external,

    'on_tags': on_tags,

    'dimmer_show': lambda: this.setState({'dimmer': True}),
    'dimmer_hide': lambda: this.setState({'dimmer': False}),

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': gallery_on_update,

    'render': gallery_render
})
