__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass,
                         LazyLoad)
from ui import ui, Slider, Error
from client import (client, ServerMsg, ItemType, ImageSize, thumbclient, Command)
from i18n import tr
import utils
from state import state

def thumbnail_on_mount():
    if this.state.item_id and this.state.size_type and this.state.item_type:
        this.get_thumb()

__pragma__('tconv')

def thumbnail_get_thumb(data=None, error=None):
    if data is not None and not error:
        cmd_id = data[str(this.state.item_id)]
        if cmd_id:
            cmd = Command(cmd_id)
            cmd.set_callback(this.set_thumb)
            cmd.poll_until_complete(500)
    elif error:
        pass
    else:
        if this.state.item_id:
            thumbclient.call_func("get_image", this.get_thumb,
                                  item_ids=[this.state.item_id],
                                  size=this.state.size_type, url=True, uri=True, item_type=this.state.item_type)
__pragma__('notconv')

def thumbnail_set_thumb(cmd):
    val = cmd.get_value()
    im = None
    if val:
        im = val['data']
    if not im:
        im = "/static/img/no-image.png"
    this.setState({'img':im, 'loading':False})

def thumbnail_render():
    img_url = "static/img/default.png"
    if this.state.img:
        img_url = this.state.img

    return h("div",e(ui.Loader, active=this.state.loading, inverted=True), e(ui.Image, src=img_url, fluid=True))

Thumbnail = createReactClass({
    'displayName': 'Thumbnail',

    'getInitialState': lambda: {'item_id':this.props.item_id,
                                'size_type':this.props.size_type,
                                'item_type':this.props.item_type,
                                'img':None,
                                'loading':True},

    'get_thumb': thumbnail_get_thumb,

    'set_thumb': thumbnail_set_thumb,

    'componentDidMount': thumbnail_on_mount,

    'render': thumbnail_render
})

def gallery_on_mount():
    if this.state.data:
        this.setState({'id':this.state.data.id})
        this.get_artists()


def gallery_get_artists(data=None, error=None):
    if data is not None and not error:
        if data:
            this.setState({"artists":data})
    elif error:
        state.app.notif("Failed to artists for item type ({}): {}".format(this.state.id, this.state.item_type), level="error")
    else:
        client.call_func("get_related_items", this.get_artists,
                            item_type=this.state.item_type,
                            item_id=this.state.data.id,
                            related_type=ItemType.Artist)

def gallery_render():
    fav = 0
    title = ""
    rating = 0
    item_id = this.state.id
    if this.state.data:
        rating = this.state.data.rating
        title = this.state.data.titles[0].js_name
        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id


    artists = []
    for a in this.state.artists:
        if len(a.names) > 0:
            artists.append(a.names[0].js_name)
    artist_el = [h("span", x) for x in artists]

    return e(ui.Card,
                    h("div",
                    e(LazyLoad, e(Thumbnail, item_id=item_id, item_type=this.state.item_type, size_type=ImageSize.Medium), once=True, height='100%'),
                    e(ui.Rating, icon="heart", size="massive", className="card-item top left", defaultRating=fav),
                    e(ui.Label, e(ui.Icon, js_name="star"), rating, className="card-item bottom left", circular=True, size="large", color="yellow"),
                    e(ui.Icon, js_name="ellipsis vertical", bordered=True, className="card-item bottom right", link=True, inverted=True),
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
                    link=True)

Gallery = createReactClass({
    'displayName': 'Gallery',

    'getInitialState': lambda: {'id':None,
                                'data':None,
                                'artists':[],
                                'item_type':ItemType.Gallery},

    'get_artists': gallery_get_artists,

    'componentWillMount': lambda: this.setState({'data':this.props.data, 'id':0}),

    'componentDidMount': gallery_on_mount,

    'render': gallery_render
})

Collection = createReactClass({
    'displayName': 'Collection',

    'getInitialState': lambda: {'id':None,
                                'data':None,
                                'items':[],
                                'item_type':ItemType.Collection},

    'render': lambda: e(ui.Card,
                        e(ui.Image, src='static/img/default.png'),
                        e(ui.Card.Content,
                          e(ui.Card.Header,"Title"),
                          e(ui.Card.Meta,"Artist"),),
                        e(ui.Card.Content,extra=True),
                        link=True)
})

def grouping_render():
    title = ""
    fav = 0
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
                    e(LazyLoad, e(Thumbnail, item_id=item_id, item_type=this.state.item_type, size_type=ImageSize.Medium), once=True, height='100%'),
                    #e(ui.Label, e(ui.Icon, js_name="star half empty"), avg_rating, className="card-item bottom left", circular=True, size="large", color="orange"),
                    e(ui.Icon, js_name="ellipsis vertical", bordered=True, className="card-item bottom right", link=True, inverted=True),
                    e(ui.Label, e(ui.Icon, js_name="block layout"), len(this.state.galleries), className="card-item top right",),
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

    'getInitialState': lambda: {'id':None,
                                'data':None,
                                'artists':[],
                                'galleries':[],
                                'item_type':ItemType.Grouping},

    'componentWillMount': lambda: this.setState({'data':this.props.data, 'id':0}),

    'render': grouping_render
})


def search_render():
    fluid = this.props.fluid
    options = [
        {'key':'gallery', 'text':'Gallery', 'value':ItemType.Gallery},
        {'key':'collection', 'text':'Collection', 'value':ItemType.Collection},
        ]
    return e(ui.Search,
                        size=this.props.size,
                        input=e(ui.Input, fluid=this.props.fluid, placeholder="Search title, artist, namespace & tags",
                                label=e(ui.Popup,
                                  e(ui.Grid, centered=True),
                                  trigger=e(ui.Label, e(ui.Icon, js_name="options"), "Search Options",),
                                  hoverable=True,
                                  on="click",
                                  hideOnScroll=True,)),
                        fluid=True,
                        icon=e(ui.Icon, js_name="search", link=True),
                        className=this.props.className)

Search = createReactClass({
    'displayName': 'Search',

    'getInitialState': lambda: {'query':'',
                                },

    'render': search_render
})


def get_items(data=None, error=None):
    if data is not None and not error:
        this.setState({"items":data, 'loading':False})
    elif error:
        state.app.notif("Failed to fetch item type: {}".format(this.props.item_type), level="error")
    else:
        item = this.props.item_type
        func_kw = { 'item_type':item,
                    'page':this.state.page,
                    'limit':this.state.limit }
        if this.props.view_filter:
            func_kw['view_filter'] = this.props.view_filter
        if item:
            client.call_func("library_view", this.get_items, **func_kw)

def item_view_on_mount():
    el = {
        ItemType.Gallery:Gallery,
        ItemType.Collection:Collection,
        ItemType.Grouping:Grouping
        }.get(this.props.item_type)
    if not el:
        state.notif("No valid item type chosen", level="error")

    this.setState({'element':el})

def item_view_render():
    items = this.state['items']
    el = this.state.element

    if not el:
        return e(Error, content="An error occured")

    return e(ui.Segment,
             e(ui.Grid,
                *[e(ui.Grid.Column, c, computer=4, tablet=4, mobile=6, largeScreen=3, widescreen=2) for c in
                  [e(LazyLoad, e(el, data=x), once=True, height='100%') for x in items]],
                padded=True,
                relaxed=True,
                stackable=True),
             basic=True,
             loading=this.state.loading
             )

ItemView = createReactClass({
    'displayName': 'ItemView',

    'getInitialState': lambda: {'page':0,
                                'limit':50,
                                'infinitescroll':False,
                                'items':[],
                                "element":None,
                                "loading":True},

    'get_items': get_items,

    'componentWillMount': item_view_on_mount,
    'componentDidMount': lambda: this.get_items(),


    'render': item_view_render
})


Page = createReactClass({
    'displayName': 'DasboardPage',

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Grid.Column,
                        e(ui.Header, tr(this, "", "Newest Additions"), as_="h4", dividing=True),
                        e(ui.Header, tr(this, "", "Artist Spotlight"), as_="h4", dividing=True),
                        e(ui.Header, tr(this, "", "Previously Read"), as_="h4", dividing=True),
                        e(ui.Header, tr(this, "", "Based On Today's Tags"), as_="h4", dividing=True),
                        e(ui.Header, tr(this, "", "Random"), as_="h4",  dividing=True),
                        e(ui.Header, tr(this, "", "Needs Tagging"), as_="h4", dividing=True),
                        e(ui.Header, tr(this, "", "Recently Rated High"), as_="h4", dividing=True),)
})

