__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass,
                         withRouter,
                         Link)
from ui import ui, Slider, Error, Pagination
from client import (client, ServerMsg, ItemType, ImageSize, thumbclient, Command)
from i18n import tr
import utils
from state import state

def thumbnail_on_update(p_props, p_state):
    if any((
        p_props.item_type != this.props.item_type,
        p_props.item_id != this.props.item_id,
        p_props.size_type != this.props.size_type,
        )):
        this.get_thumb()


__pragma__('tconv')

def thumbnail_get_thumb(data=None, error=None):
    if data is not None and not error:
        cmd_id = data[str(this.props.item_id)]
        if cmd_id:
            cmd = Command(cmd_id)
            this.setState({'active_cmd': cmd})
            cmd.set_callback(this.set_thumb)
            cmd.poll_until_complete(500)
    elif error:
        pass
    else:
        if this.state.active_cmd:
            this.state.active_cmd.stop()
            this.setState({'active_cmd': None})
        if this.props.item_id and this.props.size_type and this.props.item_type:
            thumbclient.call_func("get_image", this.get_thumb,
                                  item_ids=[this.props.item_id],
                                  size=this.props.size_type, url=True, uri=True, item_type=this.props.item_type)
            s = {'loading':True}
            if this.state.placeholder:
                s['img'] = this.state.placeholder
            this.setState(s)
__pragma__('notconv')

def thumbnail_set_thumb(cmd):
    val = cmd.get_value()
    im = None
    if val:
        im = val['data']
    if not im:
        im = "/static/img/no-image.png"
    this.setState({'img':im, 'loading':False, 'active_cmd':None})

def thumbnail_render():
    img_url = this.state.placeholder
    if this.state.img:
        img_url = this.state.img
    fluid = True
    if this.props.fluid != js_undefined:
        fluid = this.props.fluid

    if this.props.size:
        fluid = False # can't be defined together

    ex = this.props.kwargs if utils.defined(this.props.kwargs) else {}

    return h("div", e(ui.Dimmer, e(ui.Loader), active=this.state.loading, inverted=True),
             e(ui.Image, src=img_url,
               fluid=fluid,
               size=this.props.size,
               disabled=this.props.disabled,
               centered=this.props.centered,
               bordered=this.props.bordered,
               avatar=this.props.avatar,
               dimmer=this.props.dimmer,
               height=this.props.height,
               as_=this.props.as_,
               href=this.props.href,
               hidden=this.props.hidden,
               shape=this.props.shape,
               spaced=this.props.spaced,
               ui=this.props.ui,
               verticalAlign=this.props.verticalAlign,
               width=this.props.width,
               **ex
               ),
             )

Thumbnail = createReactClass({
    'displayName': 'Thumbnail',

    'getInitialState': lambda: {'img':"",
                                'loading':True,
                                'placeholder': this.props.placeholder if utils.defined(this.props.placeholder) else "/static/img/default.png",
                                'active_cmd': None,
                                },

    'get_thumb': thumbnail_get_thumb,

    'set_thumb': thumbnail_set_thumb,

    'componentDidMount': lambda: this.get_thumb(),
    'componentWillUnmount': lambda: this.state.active_cmd.stop if this.state.active_cmd else None,
    'componentDidUpdate': thumbnail_on_update,

    'render': thumbnail_render
})


def gallery_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data':this.props.data, 'id': this.props.data.id if this.props.data else None})

def gallery_render():
    fav = 0
    title = ""
    rating = 0
    artists = []
    item_id = this.state.id
    if this.state.data:
        rating = this.state.data.rating
        title = this.state.data.titles[0].js_name
        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id

        for a in this.state.data.artists:
            if len(a.names) > 0:
                artists.append(a.names[0].js_name)

    add_cls = this.props.className or ""
    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    thumb = e(Thumbnail,
              item_id=item_id,
              item_type=this.state.item_type, 
              size_type=ImageSize.Medium,
              size=this.props.size,
              )
    if link:
        thumb = e(Link, thumb, to={'pathname':'/item/gallery',
                                    'search':utils.query_to_string({'id':item_id})})

    return e(ui.Card,
                    h("div",
                    thumb,
                    e(ui.Rating, icon="heart", size="massive", className="card-item top left", rating=fav),
                    e(ui.Popup,
                        e(ui.Rating, icon="star", defaultRating=rating, maxRating=10, clearable=True),
                        trigger=e(ui.Label, rating, className="card-item bottom left", size="large", color="yellow", as_="a"),
                        hoverable=True,
                        on="click",
                        hideOnScroll=True,
                        position="left center"
                        ),
                    e(ui.Icon, js_name="ellipsis vertical", bordered=True, className="card-item bottom right", link=True, inverted=True),
                    className="card-content",
                    ),
                    e(ui.Popup,
                        trigger=e(ui.Card.Content,
                                    e(ui.Card.Header, title, className="text-ellipsis card-header"),
                                    e(ui.Card.Meta, *[h("span", x) for x in artists], className="text-ellipsis"),),
                        header=title,
                        content=h("div", *[h("span", x) for x in artists]),
                        hideOnScroll=True,
                        position="bottom center"
                                ),
                    className=add_cls,
                    link=True)

Gallery = createReactClass({
    'displayName': 'Gallery',

    'getInitialState': lambda: {'id':None,
                                'data':this.props.data,
                                'item_type':ItemType.Gallery,
                                },

    'componentWillMount': lambda: this.setState({'id':this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': gallery_on_update,

    'render': gallery_render
})

def page_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data':this.props.data, 'id': this.props.data.id if this.props.data else None})

def page_render():
    fav = 0
    title = ""
    item_id = this.state.id
    if this.state.data:
        title = str(this.state.data.number)
        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id

    add_cls = this.props.className or ""

    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    thumb = e(Thumbnail,
              item_id=item_id,
              item_type=this.state.item_type, 
              size_type=ImageSize.Medium,
              size=this.props.size,
              )
    if link:
        thumb = e(Link, thumb, to={'pathname':'/item/page',
                                    'search':utils.query_to_string({'id':item_id})})


    return e(ui.Card,
                    h("div",
                    thumb,
                    e(ui.Icon, js_name="ellipsis vertical", bordered=True, className="card-item bottom right", link=True, inverted=True),
                    className="card-content",
                    ),
                    e(ui.Card.Content, e(ui.Card.Header, e(ui.Label, title, circular=True), className="text-ellipsis card-header")),
                    className=add_cls,
                    link=True)

Page = createReactClass({
    'displayName': 'Page',

    'getInitialState': lambda: {'id':None,
                                'data':this.props.data,
                                'item_type':ItemType.Page},

    'componentWillMount': lambda: this.setState({'id':this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': page_on_update,
    'render': page_render
})

Collection = createReactClass({
    'displayName': 'Collection',

    'getInitialState': lambda: {'id':None,
                                'data':None,
                                'items':[],
                                'item_type':ItemType.Collection},

    'render': lambda: e(ui.Card,
                        e(ui.Image, src='/static/img/default.png'),
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
                    e(Thumbnail, item_id=item_id, item_type=this.state.item_type, size_type=ImageSize.Medium),
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


SearchOptions = createReactClass({
    'displayName': 'SearchOptions',

    'getInitialState': lambda: {'case':False,
                                'regex':False,
                                'whole':False,
                                'all':False,
                                'desc':False,},

    'render': lambda: e(ui.List,
                        e(ui.List.Item, e(ui.Checkbox, toggle=True, label="Case sensitive", defaultChecked=this.state.case)),
                        e(ui.List.Item, e(ui.Checkbox, toggle=True, label="Regex", defaultChecked=this.state.regex)),
                        e(ui.List.Item, e(ui.Checkbox, toggle=True, label="Match exact", defaultChecked=this.state.whole)),
                        e(ui.List.Item, e(ui.Checkbox, toggle=True, label="Match all", defaultChecked=this.state.all)),
                        e(ui.List.Item, e(ui.Checkbox, toggle=True, label="Children", defaultChecked=this.state.desc)),
                        )
})


def search_render():
    fluid = this.props.fluid

    return e(ui.Form,   
                e(ui.Search,
                        size=this.props.size,
                        input=e(ui.Input, fluid=this.props.fluid, placeholder="Search title, artist, namespace & tags",
                                label=e(ui.Popup,
                                  e(SearchOptions),
                                  trigger=e(ui.Label, e(ui.Icon, js_name="options"), "Search Options", as_="a"),
                                  hoverable=True,
                                  on="click",
                                  hideOnScroll=True,)),
                        fluid=True,
                        icon=e(ui.Icon, js_name="search", link=True, onClick=this.on_search),
                        onSearchChange=this.on_search_change,
                        defaultValue = utils.get_query("search", "")
                        ),
                className=this.props.className,
                onSubmit=this.on_search
                )

def on_search_change(e, d):
    this.search_data = d.value
    if this.props.on_key:
        clearTimeout(this.search_timer_id)
        this.search_timer_id = setTimeout(this.search_timer, 400)

def on_search(e, d):
    if e is not None:
        d = this.search_data
    if this.props.query and this.props.history:
        utils.go_to(this.props.history, query={'search':d})
    if this.props.on_search:
        this.props.on_search(d)

def on_search_timer():
    __pragma__("tconv")
    if this.search_data:
        this.on_search(None, this.search_data)
    __pragma__("notconv")

Search = createReactClass({
    'displayName': 'Search',

    'getInitialState': lambda: {'query':'',
                                },

    'search_data':[],
    'search_timer_id':0,
    'search_timer': on_search_timer,

    'on_search_change': on_search_change,

    'on_search': on_search,

    'render': search_render
})

def ItemViewBase(props):
    pagination = e(ui.Grid.Row,
                   e(ui.Responsive,
                       e(Pagination,
                         limit=2,
                         pages=props.item_count/props.limit,
                         current_page=props.page,
                         on_change=props.set_page,
                         query=True,
                         scroll_top=True,
                         size="tiny"),
                       maxWidth=578,
                     ),
                   e(ui.Responsive,
                       e(Pagination,
                         pages=props.item_count/props.limit,
                         current_page=props.page,
                         on_change=props.set_page,
                         query=True,
                         scroll_top=True),
                       minWidth=579,
                     ),
                   centered=True,
                   )

    lscreen = 3
    wscreen = 2
    if props.container:
        lscreen = wscreen = 4

    els = props.children
    if not els:
        els = []

    add_el = []

    if props.label:
        add_el.append(e(ui.Label, props.label, e(ui.Label.Detail, props.item_count), attached="top"))

    return e(ui.Segment,
             *add_el,
             e(ui.Grid,
               pagination,
                *[e(ui.Grid.Column, c, computer=4, tablet=3, mobile=6, largeScreen=lscreen, widescreen=wscreen) for c in els],
                pagination,
                padded="vertically",
                centered=True,
                ),
             basic=True,
             loading=props.loading,
             secondary=props.secondary,
             tertiary=props.tertiary,
             )

def get_items(data=None, error=None):
    if data is not None and not error:
        this.setState({"items":data, 'loading':False})
    elif error:
        state.app.notif("Failed to fetch item type: {}".format(this.props.item_type), level="error")
    else:
        item = this.props.item_type
        func_kw = { 'item_type':item,
                    'page': max(int(this.state.page)-1, 0),
                    'limit':this.props.limit or this.state.default_limit}
        if utils.defined(this.props.view_filter):
            func_kw['view_filter'] = this.props.view_filter
        if this.state.search_query:
            func_kw['search_query'] = this.state.search_query
        if this.props.related_type:
            func_kw['related_type'] = this.props.related_type
        if this.props.item_id:
            func_kw['item_id'] = this.props.item_id
        if item:
            client.call_func("library_view", this.get_items, **func_kw)
            this.setState({'loading':True})

def get_items_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"item_count":data['count']})
    elif error:
        pass
    else:
        item = this.props.item_type
        func_kw = { 'item_type':item }
        if this.props.view_filter:
            func_kw['view_filter'] = this.props.view_filter
        if this.state.search_query:
            func_kw['search_query'] = this.state.search_query
        if this.props.related_type:
            func_kw['related_type'] = this.props.related_type
        if this.props.item_id:
            func_kw['item_id'] = this.props.item_id

        if item:
            client.call_func("get_view_count", this.get_items_count, **func_kw)


def get_element():
    el = {
        ItemType.Gallery:Gallery,
        ItemType.Collection:Collection,
        ItemType.Grouping:Grouping,
        ItemType.Page:Page,
        }.get(this.props.related_type or this.props.item_type)
    if not el:
        state.notif("No valid item type chosen", level="error")

    this.setState({'element':el})

def item_view_on_update(p_props, p_state):
    if p_props.item_type != this.props.item_type:
        this.get_element()


    if p_props.search_query != this.props.search_query:
        this.setState({'search_query':this.props.search_query})

    if any((
        p_props.item_type != this.props.item_type,
        p_props.related_type != this.props.related_type,
        p_props.item_id != this.props.item_id,
        p_props.view_filter != this.props.view_filter,
        p_props.search_query != this.props.search_query,
        p_state.search_query != this.state.search_query,
        p_props.limit != this.props.limit,
        )):
        this.setState({'page':1})
        this.get_items_count()

    if any((
        p_props.item_type != this.props.item_type,
        p_props.related_type != this.props.related_type,
        p_props.item_id != this.props.item_id,
        p_props.view_filter != this.props.view_filter,
        p_props.search_query != this.props.search_query,
        p_state.search_query != this.state.search_query,
        p_props.limit != this.props.limit,
        p_state.page != this.state.page,
        )):
        this.get_items()

def item_view_render():
    items = this.state['items']
    el = this.state.element
    limit = this.props.limit or this.state.default_limit
    if not el:
        return e(Error, content="An error occured")

    return e(ItemViewBase,
             [e(el, data=x, className="medium-size", key=n) for n, x in enumerate(items)],
             loading=this.state.loading,
             secondary=this.props.secondary,
             tertiary=this.props.tertiary,
             container=this.props.container,
             item_count=this.state.item_count,
             limit=limit,
             page=this.state.page,
             set_page=this.set_page,
             label=this.props.label,
             )

ItemView = createReactClass({
    'displayName': 'ItemView',

    'getInitialState': lambda: {'page': int(utils.get_query("page", 1)) or 1,
                                'search_query': utils.get_query("search", "") or this.props.search_query,
                                'infinitescroll':False,
                                'default_limit': 30,
                                'items':[],
                                "element":None,
                                "loading":True,
                                "item_count":1,
                                },

    'get_items_count': get_items_count,
    'get_items': get_items,
    'get_element': get_element,
    
    'set_page': lambda p: this.setState({'page':p}),

    'componentWillMount': lambda: this.get_element(),
    'componentDidMount': lambda: all((this.get_items(), this.get_items_count())),
    'componentDidUpdate': item_view_on_update, 

    'render': item_view_render
})

ViewOptions = createReactClass({
    'displayName': 'ViewOptions',

    'getInitialState': lambda: {'page':0,
                                'limit':50,
                                'infinitescroll':False,
                                'items':[],
                                "element":None,
                                "loading":True},


    'render': lambda: h("div")
})

def itemdropdown_change(e, d):
    if this.props.query:
        utils.go_to(this.props.history, query={'item_type':d.value}, push=False)
    if this.props.on_change:
        this.props.on_change(e, d)

def itemdropdown_render():
    props = this.props
    item_options = [
        {'text':"Collection", 'value':ItemType.Collection},
        {'text':"Gallery", 'value':ItemType.Gallery},
        ]
    return e(ui.Dropdown, placeholder="Item Type", selection=True, options=item_options, item=True,
             defaultValue=ItemType.Gallery if props.value == ItemType.Grouping else props.value, onChange=this.item_change)

ItemDropdown = createReactClass({
    'displayName': 'ItemDropdown',

    'item_change': itemdropdown_change,

    'render': itemdropdown_render
})

def SortDropdown(props):
    item_options = [
        ]
    return e(ui.Dropdown, placeholder="Sort by", selection=True, item=True, options=item_options, defaultValue=props.value, onChange=props.on_change)

def FilterDropdown(props):
    item_options = [
        ]
    return e(ui.Dropdown, placeholder="Filter", selection=True, item=True, options=item_options, defaultValue=props.value, onChange=props.on_change)


__pragma__("kwargs")
def item_view_menu(on_item_change=None, default_item=None, on_search=None):
    return [e(ui.Menu.Item, e(withRouter(ItemDropdown), on_change=on_item_change, value=default_item, query=True), fitted=True),
            e(ui.Menu.Menu,
                e(ui.Menu.Item,
                    e(withRouter(Search), size="small", fluid=True, className="fullwidth", on_search=on_search, query=True), className="fullwidth",),
                position="left",
                className="fullwidth"),
            e(ui.Menu.Item, e(ui.Icon, js_name="sort"), e(SortDropdown, on_change=None, value=None), fitted=True),
            e(ui.Menu.Item, e(ui.Icon, js_name="filter"), e(FilterDropdown, on_change=None, value=None), fitted=True),
            e(ui.Popup,
                e(ui.Grid, centered=True),
                trigger=e(ui.Menu.Item, e(ui.Icon, js_name="options"), "View Options",),
                hoverable=True,
                on="click",
                flowing=True,
                ),
            ]
__pragma__("nokwargs")

def itemviewpage_render():
    return e(ItemView,
                        item_type=this.state.item_type,
                        view_filter=this.props.view_type,
                        search_query=this.state.search_query)

ItemViewPage = createReactClass({
    'displayName': 'ItemViewPage',

    'on_item_change': lambda e, d: this.setState({'item_type':d.value}),

    'on_search': lambda v: this.setState({'search_query':v}),

    'update_menu': lambda: state.app.set_menu_contents(
        item_view_menu(
            on_item_change=this.on_item_change,
            default_item=this.state.item_type,
            on_search=this.on_search,
            )),

    'componentWillMount': lambda: this.update_menu(),

    'componentDidUpdate': lambda p_p, p_s: this.update_menu() if p_p.view_type != this.props.view_type else None,

    'getInitialState': lambda: {'item_type': int(utils.get_query("item_type", ItemType.Gallery)),
                                'search_query':""},

    'render': itemviewpage_render
})

