__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             React,
                             createReactClass,
                             withRouter,
                             Link)
from src.ui import ui, Slider, Error, Pagination
from src.client import (client, ServerMsg, ItemType, ImageSize, thumbclient, Command)
from src.i18n import tr
from src.state import state
from src import utils


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
            s = {'loading': True}
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
    this.setState({'img': im, 'loading': False, 'active_cmd': None})


def thumbnail_render():
    img_url = this.state.placeholder
    if this.state.img:
        img_url = this.state.img
    fluid = True
    if this.props.fluid != js_undefined:
        fluid = this.props.fluid

    if this.props.size:
        fluid = False  # can't be defined together

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

    'getInitialState': lambda: {'img': "",
                                'loading': True,
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
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


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
        thumb = e(Link, thumb, to={'pathname': '/item/gallery',
                                   'search': utils.query_to_string({'id': item_id})})

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
                   position="left center"
                 ),
                 e(ui.Icon, js_name="ellipsis vertical", bordered=True,
                   className="card-item bottom right", link=True, inverted=True),
               className="card-content",
               ),
             e(ui.Popup,
               trigger=e(ui.Card.Content,
                         e(ui.Card.Header, title, className="text-ellipsis card-header"),
                         e(ui.Card.Meta, *[h("span", x) for x in artists], className="text-ellipsis"),),
               header=title,
               content=h("div", *[h("span", x) for x in artists]),
               hideOnScroll=True,
               hoverable=False,
               position="bottom center"
               ),
             className=add_cls,
             link=True)

Gallery = createReactClass({
    'displayName': 'Gallery',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                },

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': gallery_on_update,

    'render': gallery_render
})


def page_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


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
        thumb = e(Link, thumb, to={'pathname': '/item/page',
                                   'search': utils.query_to_string({'id': item_id})})

    return e(ui.Card,
             h("div",
               thumb,
               e(ui.Icon, js_name="ellipsis vertical", bordered=True,
                 className="card-item bottom right", link=True, inverted=True),
               className="card-content",
               ),
             e(ui.Card.Content, e(ui.Card.Header, e(ui.Label, title, circular=True), className="text-ellipsis card-header")),
             className=add_cls,
             link=True)

Page = createReactClass({
    'displayName': 'Page',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Page},

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': page_on_update,
    'render': page_render
})

Collection = createReactClass({
    'displayName': 'Collection',

    'getInitialState': lambda: {'id': None,
                                'data': None,
                                'items': [],
                                'item_type': ItemType.Collection},

    'render': lambda: e(ui.Card,
                        e(ui.Image, src='/static/img/default.png'),
                        e(ui.Card.Content,
                          e(ui.Card.Header, "Title"),
                          e(ui.Card.Meta, "Artist"),),
                        e(ui.Card.Content, extra=True),
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
})

SearchOptions = createReactClass({
    'displayName': 'SearchOptions',

    'render': lambda: e(ui.List,
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change, toggle=True,
                                          js_name="case", label="Case sensitive", checked=this.props.case_)),
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change,
                                          toggle=True, js_name="regex", label="Regex", checked=this.props.regex)),
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change, toggle=True,
                                          js_name="whole", label="Match exact", checked=this.props.whole)),
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change,
                                          toggle=True, js_name="all", label="Match all", checked=this.props.all)),
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change, toggle=True,
                                          js_name="desc", label="Children", checked=this.props.desc)),
                        )
})


def search_get_config(data=None, error=None):
    if data is not None and not error:
        options = {"case": data['search.case_sensitive'],
                   "all": data['search.match_all_terms'],
                   "regex": data['search.regex'],
                   "whole": data['search.match_whole_words'],
                   "desc": data['search.descendants'],
                   }
        this.setState(options)
    elif error:
        state.app.notif("Failed to retrieve search configuration", level="warning")
    else:
        client.call_func("get_config", this.get_config, cfg={'search.case_sensitive': False,
                                                             'search.match_all_terms': False,
                                                             'search.regex': False,
                                                             'search.descendants': False,
                                                             'search.match_whole_words': False,
                                                             })


def search_render():
    fluid = this.props.fluid
    return e(ui.Form,
             e(ui.Search,
               size=this.props.size,
               input=e(ui.Input,
                       fluid=this.props.fluid,
                       placeholder="Search title, artist, namespace & tags",
                       label=e(ui.Popup,
                               e(SearchOptions,
                                 history=this.props.history,
                                 query=this.props.query,
                                 on_change=this.on_search_options,
                                 case_=this.state['case'],
                                 regex=this.state.regex,
                                 whole=this.state.whole,
                                 all=this.state.all,
                                 desc=this.state.all,
                                 ),
                               trigger=e(ui.Label, icon="options", as_="a"),
                               hoverable=True,
                               on="click",
                               hideOnScroll=True,)),
               fluid=True,
               icon=e(ui.Icon, js_name="search", link=True, onClick=this.on_search),
               onSearchChange=this.on_search_change,
               defaultValue=utils.get_query("search", "") if this.props.query else ''
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
        utils.go_to(this.props.history, query={'search': d})
    if this.props.on_search:
        o = {
            'regex': 'regex',
            'case': 'case_sensitive',
            'whole': 'match_whole_words',
            'all': 'match_all_terms',
            'desc': 'descendants',
        }
        __pragma__("iconv")
        options = {}
        for k in o:
            options[o[k]] = this.state[k]
        __pragma__("noiconv")
        this.props.on_search(d, options)


def on_search_timer():
    __pragma__("tconv")
    if this.search_data:
        this.on_search(None, this.search_data)
    __pragma__("notconv")


def search_option_change(e, d):
    this.setState({d.js_name: d.checked})
    if this.props.query:
        utils.go_to(this.props.history, query={d.js_name: '1' if d.checked else '0'})


Search = createReactClass({
    'displayName': 'Search',

    'getInitialState': lambda: {'query': '',
                                'case': bool(int(utils.get_query("case", 0))),
                                'regex': bool(int(utils.get_query("regex", 0))),
                                'whole': bool(int(utils.get_query("whole", 0))),
                                'all': bool(int(utils.get_query("all", 0))),
                                'desc': bool(int(utils.get_query("desc", 0))),
                                },

    'search_data': [],
    'search_timer_id': 0,
    'search_timer': on_search_timer,

    'get_config': search_get_config,

    'componentWillMount': lambda: this.get_config(),

    'on_search_change': on_search_change,

    'on_search_options': search_option_change,

    'on_search': on_search,

    'render': search_render
})


def itemviewbase_render():
    props = this.props
    pagination = e(ui.Grid.Row,
                   e(ui.Responsive,
                       e(Pagination,
                         limit=1,
                         pages=props.item_count / props.limit,
                         current_page=props.page,
                         on_change=props.set_page,
                         query=True,
                         scroll_top=True,
                         size="tiny"),
                       maxWidth=578,
                     ),
                   e(ui.Responsive,
                       e(Pagination,
                         pages=props.item_count / props.limit,
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

    count_el = []

    if (not utils.defined(props.show_count)) or props.show_count:
        count_el.append(e(ui.Grid.Column,
                          e(ui.Header,
                            e(ui.Header.Subheader,
                              # tr(this,
                              #   "ui.t-showing-count",
                              #   "Showing {}".format(props.item_count),
                              #   placeholder={'from':(props.page-1)*props.limit or 1, 'to':(props.page-1)*props.limit+props.limit, 'all':props.item_count}
                              #   ),
                              as_="h6"),
                            ),
                          textAlign="center", width=16))

    return e(ui.Segment,
             *add_el,
             e(ui.Grid,
               *count_el,
               pagination,
               *[e(ui.Grid.Column, c, computer=4, tablet=3, mobile=6, largeScreen=lscreen, widescreen=wscreen) for c in els],
               pagination,
               *count_el,
               padded="vertically",
               centered=True,
               as_=ui.Transition.Group,
               duration=1500,
               ),
             basic=True,
             loading=props.loading,
             secondary=props.secondary,
             tertiary=props.tertiary,
             )

ItemViewBase = createReactClass({
    'displayName': 'ItemViewBase',

    'render': itemviewbase_render
})

__pragma__("tconv")


def get_items(data=None, error=None):
    if data is not None and not error:
        this.setState({"items": data, 'loading': False})
    elif error:
        state.app.notif("Failed to fetch item type: {}".format(this.props.item_type), level="error")
    else:
        item = this.props.item_type
        func_kw = {'item_type': item,
                   'page': max(int(this.state.page) - 1, 0),
                   'limit': this.props.limit or this.state.default_limit}
        if utils.defined(this.props.view_filter):
            func_kw['view_filter'] = this.props.view_filter
        if this.state.search_query:
            func_kw['search_query'] = this.state.search_query
        if this.props.search_options:
            func_kw['search_options'] = this.props.search_options
        if this.props.filter_id:
            func_kw['filter_id'] = this.props.filter_id
        if this.props.related_type:
            func_kw['related_type'] = this.props.related_type
        if this.props.item_id:
            func_kw['item_id'] = this.props.item_id
        if item:
            client.call_func("library_view", this.get_items, **func_kw)
            this.setState({'loading': True})
__pragma__("notconv")

__pragma__("tconv")


def get_items_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"item_count": data['count']})
    elif error:
        pass
    else:
        item = this.props.item_type
        func_kw = {'item_type': item}
        if this.props.view_filter:
            func_kw['view_filter'] = this.props.view_filter
        if this.props.filter_id:
            func_kw['filter_id'] = this.props.filter_id
        if this.state.search_query:
            func_kw['search_query'] = this.state.search_query
        if this.props.search_options:
            func_kw['search_options'] = this.props.search_options
        if this.props.related_type:
            func_kw['related_type'] = this.props.related_type
        if this.props.item_id:
            func_kw['item_id'] = this.props.item_id

        if item:
            client.call_func("get_view_count", this.get_items_count, **func_kw)
__pragma__("notconv")


def get_element():
    el = {
        ItemType.Gallery: Gallery,
        ItemType.Collection: Collection,
        ItemType.Grouping: Grouping,
        ItemType.Page: Page,
    }.get(this.props.related_type or this.props.item_type)
    if not el:
        state.notif("No valid item type chosen", level="error")

    this.setState({'element': el})


def item_view_on_update(p_props, p_state):
    if p_props.item_type != this.props.item_type:
        this.get_element()

    if p_props.search_query != this.props.search_query:
        this.setState({'search_query': this.props.search_query})

    if any((
        p_props.item_type != this.props.item_type,
        p_props.related_type != this.props.related_type,
        p_props.item_id != this.props.item_id,
        p_props.filter_id != this.props.filter_id,
        p_props.view_filter != this.props.view_filter,
        p_props.search_options != this.props.search_options,
        p_props.search_query != this.props.search_query,
        p_state.search_query != this.state.search_query,
        p_props.limit != this.props.limit,
    )):
        this.setState({'page': 1})
        this.get_items_count()

    if any((
        p_props.item_type != this.props.item_type,
        p_props.related_type != this.props.related_type,
        p_props.item_id != this.props.item_id,
        p_props.filter_id != this.props.filter_id,
        p_props.view_filter != this.props.view_filter,
        p_props.search_options != this.props.search_options,
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
                                'infinitescroll': False,
                                'default_limit': 30,
                                'items': [],
                                "element": None,
                                "loading": True,
                                "item_count": 1,
                                },

    'get_items_count': get_items_count,
    'get_items': get_items,
    'get_element': get_element,

    'set_page': lambda p: this.setState({'page': p}),

    'componentWillMount': lambda: this.get_element(),
    'componentDidMount': lambda: all((this.get_items(), this.get_items_count())),
    'componentDidUpdate': item_view_on_update,

    'render': item_view_render
})

ViewOptions = createReactClass({
    'displayName': 'ViewOptions',

    'getInitialState': lambda: {'page': 0,
                                'limit': 50,
                                'infinitescroll': False,
                                'items': [],
                                "element": None,
                                "loading": True},


    'render': lambda: h("div")
})


def itemdropdown_change(e, d):
    if this.props.query:
        utils.go_to(this.props.history, query={'item_type': d.value}, push=False)
    if this.props.on_change:
        this.props.on_change(e, d)


def itemdropdown_render():
    props = this.props
    item_options = [
        {'text': "Collection", 'value': ItemType.Collection},
        {'text': "Gallery", 'value': ItemType.Gallery},
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
    return e(ui.Dropdown, placeholder="Sort by", selection=True, item=True,
             options=item_options, defaultValue=props.value, onChange=props.on_change)


def filterdropdown_get(data=None, error=None):
    if data is not None and not error:
        items = {}
        for d in data:
            items[d['id']] = d
        this.setState({"db_items": items, "loading": False})
    elif error:
        pass
    else:
        client.call_func("get_items", this.get_items, item_type=ItemType.GalleryFilter, limit=999)
        this.setState({"loading": True})


def filterdropdown_change(e, d):
    if this.props.query:
        utils.go_to(this.props.history, query={'filter_id': d.value}, push=False)
    if this.props.on_change:
        this.props.on_change(e, d)


def filterdropdown_render():
    item_options = [{'value': 0, "description": "No Filter", "icon": "delete"}]
    text = js_undefined
    __pragma__("iconv")
    if this.state.db_items:
        for d in this.state.db_items:
            if d == this.props.value:
                text = this.state.db_items[d]['name']
            item_options.append({'text': this.state.db_items[d]['name'], 'value': d, 'icon': "filter"})
    __pragma__("noiconv")
    return e(ui.Dropdown,
             placeholder="Filter",
             selection=True, item=True,
             options=item_options,
             text=text if text else js_undefined,
             search=True,
             allowAdditions=True,
             value=this.props.value if this.props.value else js_undefined,
             defaultValue=this.props.defaultValue,
             onChange=this.item_change,
             loading=this.state.loading,
             )

FilterDropdown = createReactClass({
    'displayName': 'FilterDropdown',

    'getInitialState': lambda: {'db_items': None, 'loading': False},

    'item_change': filterdropdown_change,
    'get_items': filterdropdown_get,
    'componentDidMount': lambda: this.get_items(),

    'render': filterdropdown_render
})

__pragma__("kwargs")


def item_view_menu(on_item_change=None, on_filter_change=None, default_item=None, on_search=None, default_filter=None):
    return [e(ui.Menu.Item, e(withRouter(ItemDropdown), on_change=on_item_change, value=default_item, query=True), fitted=True),
            e(ui.Menu.Menu,
                e(ui.Menu.Item,
                    e(withRouter(Search), size="small", fluid=True, className="fullwidth", on_search=on_search, query=True), className="fullwidth",),
                position="left",
                className="fullwidth"),
            e(ui.Menu.Item, e(ui.Icon, js_name="sort"), e(SortDropdown, on_change=None, value=None), fitted=True),
            e(ui.Menu.Item, e(ui.Icon, js_name="filter"), e(withRouter(FilterDropdown),
                                                            on_change=on_filter_change, value=default_filter, query=True), fitted=True),
            e(ui.Popup,
                e(ui.Grid, centered=True),
                trigger=e(ui.Menu.Item, e(ui.Icon, js_name="options", size="large"), icon=True),
                hoverable=True,
                on="click",
                flowing=True,
              ),
            ]
__pragma__("nokwargs")


def itemviewpage_update(p_p, p_s):
    if any((
        p_p.view_type != this.props.view_type,
        p_s.filter_id != this.state.filter_id,
    )):
        this.update_menu()


def itemviewpage_render():
    return e(ItemView,
             item_type=this.state.item_type,
             view_filter=this.props.view_type,
             search_query=this.state.search_query,
             filter_id=this.state.filter_id,
             search_options=this.state.search_options
             )

ItemViewPage = createReactClass({
    'displayName': 'ItemViewPage',

    'on_item_change': lambda e, d: this.setState({'item_type': d.value}),

    'on_filter_change': lambda e, d: this.setState({'filter_id': d.value}),

    'on_search': lambda s, o: this.setState({'search_query': s, 'search_options': o}),

    'update_menu': lambda: state.app.set_menu_contents(
        item_view_menu(
            on_item_change=this.on_item_change,
            on_filter_change=this.on_filter_change,
            default_item=this.state.item_type,
            default_filter=this.state.filter_id,
            on_search=this.on_search,
        )),

    'componentWillMount': lambda: this.update_menu(),

    'componentDidUpdate': itemviewpage_update,

    'getInitialState': lambda: {'item_type': int(utils.get_query("item_type", ItemType.Gallery)),
                                'filter_id': int(utils.get_query("filter_id", 0)),
                                'search_query': "",
                                'search_options': {},
                                },

    'render': itemviewpage_render
})
