__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
from src.ui import ui
from src.client import (ItemType, ImageSize, client)
from src.state import state
from src.single import thumbitem, artistitem
from src import utils
from src.views import tagview


def on_tags(data):
    this.setState({'tags': data})


def gallery_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})

__pragma__("tconv")


def open_external():
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
    info = ""
    inbox = False

    if this.state.data:
        read_count = this.state.data.times_read
        rating = this.state.data.rating
        title = this.state.data.titles[0].js_name
        info = this.state.data.info
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

    thumb = e(thumbitem.Thumbnail,
              item_id=item_id,
              item_type=this.state.item_type,
              size_type=ImageSize.Medium,
              size=this.props.size,
              )
    if link:
        thumb = e(Link, thumb, to={'pathname': '/item/gallery',
                                   'search': utils.query_to_string({'id': item_id})})

    rows = []

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, title, as_="h3"), colSpan="2", textAlign="center",
                    verticalAlign="middle")))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, info, as_="h5"), colSpan="2")))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, "Artist(s):", as_="h5"), collapsing=True),
                  e(ui.Table.Cell, *(e(artistitem.ArtistLabel, data=x) for x in artists))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, "Times read:", as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, read_count, circular=True))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, "Tags:", as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(tagview.TagView, item_id=item_id, item_type=this.state.item_type,
                                     data=this.state.tags, on_tags=this.on_tags))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, "URL(s):", as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.List, *[e(ui.List.Item, h("span", h("a", x, href=x, target="_blank"), e(ui.List.Icon, js_name="external share"))) for x in urls]))))


    menu_options = []
    if this.props.external_viewer:
        menu_options.append({'selected':False, 'key':'read', 'text':"Read", 'onClick':this.open_external})
    else:
        menu_options.append({'selected':False, 'key':'read', 'text':"Read", 'as':Link, 'to':utils.build_url("/item/page", {'gid': item_id}, keep_query=False)})
    menu_options.append({'selected':False, 'key':'later', 'text':"Save for later", 'icon':"history"})
    menu_options.append({'selected':False, 'key':'add_filter', 'text':"Add to filter", 'icon':"filter"})
    if inbox:
        menu_options.append({'selected':False, 'key':'library', 'text':"Send to Library", 'icon':"grid layout"})
    menu_options.append({'selected':False, 'key':'trash', 'text':"Send to Trash", 'icon':"trash"})


    return e(ui.Card,
             h("div",
               thumb,
               e(ui.Rating, icon="heart", size="massive", className="card-item top left", rating=fav),
               e(ui.Popup,
                 e(ui.Rating, icon="star", defaultRating=rating, maxRating=10, clearable=True),
                 trigger=e(
                     ui.Label,
                     rating,
                     className="card-item bottom left",
                     size="large",
                     color="yellow",
                     as_="a"),
                   hoverable=True,
                   on="click",
                   hideOnScroll=True,
                   position="left center",
                 ),
               e(ui.Dropdown,
                 options=menu_options,
                   className="card-item bottom right",
                   icon=e(ui.Icon, js_name="ellipsis vertical", bordered=True, link=True, inverted=True),
                   trigger=h("span"),
                   pointing=True,
                   selectOnBlur=False,
                 ),
               className="card-content",
               ),
             e(ui.Popup,
               trigger=e(ui.Card.Content,
                         e(ui.Card.Header, title, className="text-ellipsis card-header"),
                         e(ui.Card.Meta, *[h("span", x) for x in artist_names], className="text-ellipsis"),
                         ),
               content=e(ui.Table,
                         e(ui.Table.Body,
                           *rows
                           ),
                         basic="very",
                         size="small"
                         ),
               hideOnScroll=True,
               hoverable=True,
               position="bottom center",
               wide="very",
               on="click"
               ),
             className=add_cls,
             link=True)

Gallery = createReactClass({
    'displayName': 'Gallery',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                'tags': this.props.tags,
                                },
    'on_tags': on_tags,
    'open_external': open_external,

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': gallery_on_update,

    'render': gallery_render
})
