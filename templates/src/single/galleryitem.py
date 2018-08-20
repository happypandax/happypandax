from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
from src import utils
from src.state import state
from src.ui import ui
from src.client import (ItemType, ImageSize, client)
from src.single import thumbitem
from src.selectors import filterselector
from src.propsviews import gallerypropsview
from src.i18n import tr
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
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


def read_event(e, d):
    if this.state.data:
        client.call_func("gallery_read_event", None, item_id=this.state.data.id)


def update_metatags(mtags):
    if this.state.data:
        client.call_func("update_metatags", None, item_type=ItemType.Gallery,
                         item_id=this.state.data.id, metatags=mtags)
        d = utils.JSONCopy(this.state.data)
        d.metatags = dict(d.metatags)
        d.metatags.update(mtags)
        this.setState({'data': d})


__pragma__("notconv")


def get_item(data=None, error=None):
    if not this.mounted:
        return
    if data is not None and not error:
        this.setState({"data": data,
                       "id": data.id,
                       })

    elif error:
        state.app.notif("Failed to fetch item ({})".format(this.state.id), level="error")
    else:
        item_id = this.state.id
        item = this.state.item_type
        if item and item_id:
            client.call_func("get_item", this.get_item, item_type=item, item_id=item_id)


def gallery_rate(e, d):
    e.preventDefault()
    rating = d.rating
    if this.state.data.id:
        client.call_func("update_item", item_type=this.state.item_type,
                         item={'id': this.state.data.id, 'rating': rating})
    this.setState({'data': utils.update_object("rating", this.state.data, rating)})
    this.get_item()


def gallery_render():
    fav = 0
    title = ""
    rating = 0
    urls = []
    artist_names = []
    item_id = this.state.id
    inbox = False
    data = this.state.data
    read_mtag = False
    later_mtag = False

    if data:
        if data.rating:
            rating = data.rating
        if data.preferred_title:
            title = data.preferred_title.js_name
        if data.metatags:
            inbox = data.metatags.inbox
            read_mtag = data.metatags.read
            later_mtag = data.metatags.readlater

            if data.metatags.favorite:
                fav = 1
        if not item_id and data.id:
            item_id = data.id

        if data.artists:
            for a in data.artists:
                if len(a.names) > 0:
                    artist_names.append(a.names[0].js_name)

        if data.urls:
            for u in data.urls:
                urls.append(u.js_name)

    gallery_url = '/item/gallery/' + str(item_id)

    add_cls = this.props.className or ""
    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    read_button_args = {}
    read_button_args['onClick'] = this.on_read
    if not this.props.external_viewer:
        read_button_args['as'] = Link
        read_button_args['to'] = "/item/gallery/{}/page/1".format(item_id)

    thumb = e(thumbitem.Thumbnail,
              item_id=item_id,
              centered=True,
              blur=this.props.blur,
              item_type=this.state.item_type,
              size_type=this.props.size_type if this.props.size_type else ImageSize.Medium,
              size=this.props.size,
              dimmer=e(ui.Dimmer,
                       active=this.state.dimmer,
                       content=e(ui.Responsive,
                                 e(ui.List,
                                   e(ui.List.Item, e(ui.Button, e(ui.Icon, js_name="envelope open outline"), tr(this, "ui.b-read", "Read"),
                                                     primary=True, size="tiny", **read_button_args)),
                                   e(ui.List.Item, e(ui.Button, e(ui.Icon, js_name="bookmark outline"), tr(this, "ui.b-save-later", "Save for later"), size="tiny") if not inbox else
                                     e(ui.Button, e(ui.Icon, js_name="grid layout"), tr(this, "ui.b-send-library", "Send to library"), onClick=this.send_to_library, color="green", size="tiny")),
                                   ),
                                 minWidth=900,
                                 ),
                       inverted=True),
              )
    if link:
        thumb = e(Link, thumb, to={'pathname': gallery_url,
                                   'state': {'gallery': data},
                                   })

    menu_options = []
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-read", "Read"),
                          icon="envelope open outline", **read_button_args))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-save-later", "Save for later"),
                          icon="bookmark outline", onClick=this.read_later))
    if inbox:
        menu_options.append(e(ui.List.Item, content=tr(
            this, "ui.b-send-library", "Send to library"), onClick=this.send_to_library, icon="grid layout"))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-add-to-filter", "Add to filter"),
                          icon="filter", onClick=this.toggle_filter))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-add-to-collection",
                                                   "Add to collection"), icon="plus square outline"))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-add-to-series", "Add to series"), icon="add square"))
    menu_options.append(e(ui.List.Item, content=tr(this, "ui.b-send-trash", "Send to Trash"),
                          icon="trash", onClick=this.send_to_trash))

    add_to_filter_el = e(ui.Modal,
                         content=e(filterselector.FilterSelector,
                                   item_type=this.state.item_type,
                                   item_id=item_id,
                                   ),
                         dimmer="inverted",
                         size="small",
                         closeOnDocumentClick=True,
                         centered=False,
                         closeIcon=True,
                         open=this.state.filter_open,
                         onClose=this.toggle_filter,
                         actions=[{'content': tr(this, "ui.b-close", "close")}]
                         )

    a_names = artist_names

    return e(ui.Card,
             add_to_filter_el,
             e(ui.Dimmer.Dimmable,
                 h("div",
                   thumb,
                   e(ui.Rating, icon="heart", onRate=this.favorite, size="massive",
                     className="card-item top left above-dimmer", rating=fav),
                   e(ui.Popup,
                     e(ui.Rating,
                       onRate=this.rate,
                       icon="star",
                       defaultRating=rating,
                       maxRating=10,
                       clearable=True,
                       className=""),
                     trigger=e(
                         ui.Label,
                         rating,
                         className="card-item bottom left above-dimmer",
                         size="small",
                         color="orange",
                         basic=True,
                         as_="a"),
                     hoverable=True,
                     on="click",
                     hideOnScroll=True,
                     position="left center",
                     ),
                   h("div",
                       *([e(ui.Icon,
                            js_name="inbox",
                            title=tr(this, "ui.t-inboxed-gallery", "This gallery is in your inbox"),
                            bordered=True,
                            inverted=True,
                            size="small",
                            link=True,
                            )] if inbox else []),
                       *([e(ui.Icon,
                            js_name="bookmark",
                            title=tr(this, "ui.b-save-later", "Save for later"),
                            bordered=True,
                            inverted=True,
                            size="small",
                            link=True,
                            )] if later_mtag else []),
                       *([e(ui.Icon,
                            js_name="eye slash outline",
                            title=tr(this, "ui.t-unread-gallery", "This gallery has not been read yet"),
                            bordered=True,
                            inverted=True,
                            size="small",
                            link=True,
                            )] if not read_mtag else []),
                       className="card-item top right above-dimmer",
                     ),
                   h("div",
                       e(ui.Popup,
                         e(ui.List, *menu_options, selection=True, relaxed=True),
                           trigger=e(ui.Icon,
                                     js_name="ellipsis vertical",
                                     bordered=True,
                                     link=True,
                                     inverted=True,
                                     onClick=this.toggle_options,
                                     ),
                           hoverable=True,
                           on="click",
                           hideOnScroll=True,
                           position="right center",
                           open=this.state.options_open,
                           onClose=this.toggle_options,
                         ),
                       className="card-item bottom right above-dimmer",
                     ),
                   className="card-content",
                   ),
                 dimmed=this.state.dimmer,
                 onMouseEnter=this.dimmer_show,
                 onMouseLeave=this.dimmer_hide,
               ),
             e(ui.Modal,
               e(ui.Modal.Content,
                 e(gallerypropsview.GalleryProps,
                   compact=True,
                   data=data,
                   tags=this.state.tags,
                   on_tags=this.on_tags,
                   on_rate=this.rate,
                   size="small"),
                 ),
               trigger=e(ui.Card.Content,
                         e(ui.Card.Header, title, className="text-ellipsis card-header"),
                         e(ui.Card.Meta, *[h("span", x) for x in a_names], className="text-ellipsis"),
                         ),
               # dimmer="inverted",
               size="small",
               closeOnDocumentClick=True,
               closeIcon=True,
               centered=False,
               ),
             centered=this.props.centered,
             className=add_cls,
             # color="pink",
             link=True)


Gallery = createReactClass({
    'displayName': 'Gallery',

    'getInitialState': lambda: {'id': this.props.data.id if this.props.data else None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                'tags': this.props.tags,
                                'dimmer': False,
                                'options_open': False,
                                'filter_open': False,
                                },
    'open_external': open_external,

    'read_event': read_event,

    'on_read': lambda e, d: all((this.read_event(e, d), this.open_external(e, d) if this.props.external_viewer else None)),

    'on_tags': on_tags,
    'update_metatags': update_metatags,
    'get_item': get_item,
    'rate': gallery_rate,
    'favorite': lambda e, d: all((this.update_metatags({'favorite': bool(d.rating)}),
                                  this.get_item(),
                                  e.preventDefault())),
    'send_to_library': lambda e, d: all((this.update_metatags({'inbox': False}),
                                         this.props.remove_item(
        this.props.data or this.state.data) if this.props.remove_item else None,
        e.preventDefault())),
    'send_to_trash': lambda e, d: all((this.update_metatags({'trash': True}),
                                       this.props.remove_item(
        this.props.data or this.state.data) if this.props.remove_item else None,
        e.preventDefault())),
    'restore_from_trash': lambda e, d: all((this.update_metatags({'trash': False}),
                                            e.preventDefault())),
    'read_later': lambda e, d: all((this.update_metatags({'readlater': True}),
                                    e.preventDefault())),

    'toggle_options': lambda: this.setState({'options_open': not this.state.options_open}),
    'toggle_filter': lambda: all((this.setState({'filter_open': not this.state.filter_open}), this.toggle_options() if this.state.options_open else None)),
    'dimmer_show': lambda: this.setState({'dimmer': True}),
    'dimmer_hide': lambda: this.setState({'dimmer': False}),

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': gallery_on_update,

    'render': gallery_render
}, pure=True)
