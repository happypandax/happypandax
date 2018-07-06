from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui
from src.client import (client, ItemType, ViewType)
from src.i18n import tr
from src.state import state
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = locationStorage = sessionStorage = None
Date = None
__pragma__('noskip')

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
                                          toggle=True, js_name="all", label="Match all terms", checked=this.props.all)),
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change, toggle=True,
                                          js_name="desc", label="Match on children", checked=this.props.desc)),
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change, toggle=True,
                                          js_name="suggest", label="Show suggestions", checked=this.props.suggest)),
                        e(ui.List.Item, e(ui.Checkbox, onChange=this.props.on_change, toggle=True,
                                          js_name="on_key", label="Dynamic search", checked=this.props.on_key)),
                        )
})


def search_get_config(data=None, error=None):
    if data is not None and not error:
        options = {"case": utils.storage.get("search_case", data['search.case_sensitive']),
                   "all": utils.storage.get("search_all", data['search.match_all_terms']),
                   "regex": utils.storage.get("search_regex", data['search.regex']),
                   "whole": utils.storage.get("search_whole", data['search.match_whole_words']),
                   "desc": utils.storage.get("search_desc", data['search.descendants']),
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
    cls_name = ""
    if this.props.fluid:
        cls_name = "fullwidth"
    if this.props.className:
        cls_name += " " + this.props.className
    return h("form",
             e(ui.Search,
               size=this.props.size,
               input=e(ui.Input,
                       fluid=this.props.fluid,
                       transparent=this.props.transparent if utils.defined(this.props.transparent) else True,
                       placeholder=tr(this, "ui.t-search-main-placeholder", "Search title, artist, namespace & tags"),
                       label=e(ui.Popup,
                               e(SearchOptions,
                                 history=this.props.history,
                                 query=this.props.query,
                                 on_change=this.on_search_options,
                                 case_=this.state['case'],
                                 regex=this.state.regex,
                                 whole=this.state.whole,
                                 all=this.state.all,
                                 desc=this.state.desc,
                                 suggest=this.state.suggest,
                                 on_key=this.state.on_key,
                                 ),
                               trigger=e(ui.Button, icon=e(ui.Icon.Group,
                                                           e(ui.Icon, js_name="options"),
                                                           e(ui.Icon, js_name="search", corner=True)),
                                         js_type="button", basic=True, size=this.props.size),
                               hoverable=True,
                               on="click",
                               hideOnScroll=True,),
                       ),
               minCharacters=3,
               fluid=this.props.fluid,
               action={'icon': 'search'},
               open=this.state.suggest if not this.state.suggest else js_undefined,
               onSearchChange=this.on_search_change,
               defaultValue=this.state.query
               ),
             className=cls_name,
             onSubmit=this.on_search
             )


def on_search_change(e, d):
    this.search_data = d.value
    if this.state.on_key:
        clearTimeout(this.search_timer_id)
        this.search_timer_id = setTimeout(this.search_timer, 400)


def on_search(e, d):
    e.preventDefault()
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
    this.on_search(None, this.search_data)


def search_option_change(e, d):
    this.setState({d.js_name: d.checked})
    if this.props.query:
        utils.storage.set("search_{}".format(d.js_name), d.checked)
        utils.go_to(this.props.history, query={d.js_name: '1' if d.checked else '0'})


Search = createReactClass({
    'displayName': 'Search',

    'getInitialState': lambda: {'query': utils.get_query("search", this.props.search_query) if this.props.query else this.props.search_query,
                                'case': utils.storage.get("search_case", bool(int(utils.get_query("case", 0)))),
                                'regex': utils.storage.get("search_regex", bool(int(utils.get_query("regex", 0)))),
                                'whole': utils.storage.get("search_whole", bool(int(utils.get_query("whole", 0)))),
                                'all': utils.storage.get("search_all", bool(int(utils.get_query("all", 0)))),
                                'desc': utils.storage.get("search_desc", bool(int(utils.get_query("desc", 0)))),
                                'suggest': utils.storage.get("search_suggest", bool(int(utils.get_query("suggest", 1)))),
                                'on_key': utils.storage.get("search_on_key", bool(int(utils.get_query("on_key", 0)))),
                                },

    'search_data': "",
    'search_timer_id': 0,
    'search_timer': on_search_timer,

    'get_config': search_get_config,

    'componentWillMount': lambda: this.get_config(),

    'on_search_change': on_search_change,

    'on_search_options': search_option_change,

    'on_search': on_search,

    'render': search_render
})


__pragma__("tconv")

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


def itembuttons_change(e, d):
    if this.props.query:
        utils.go_to(this.props.history, query={'item_type': d.value}, push=False)
    if this.props.on_change:
        this.props.on_change(e, d)


def itembuttons_render():
    ch = this.props.children
    if not isinstance(ch, list):
        ch = [ch]
    return e(ui.Button.Group,
             *ch,
             e(ui.Button, tr(this, "general.db-item-collection", "Collection"),
               value=ItemType.Collection,
               onClick=this.item_change,
               primary=True,
               basic=this.props.value == ItemType.Collection,
               ),
             e(ui.Button, tr(this, "general.db-item-gallery", "Gallery"),
               value=ItemType.Gallery,
               onClick=this.item_change,
               primary=True,
               basic=this.props.value == ItemType.Gallery,
               ),
             toggle=True,
             basic=True,
             size=this.props.size if utils.defined(this.props.size) else "small"
             )


ItemButtons = createReactClass({
    'displayName': 'ItemButtons',

    'item_change': itembuttons_change,

    'render': itembuttons_render
})


def sortdropdown_get(data=None, error=None):
    if data is not None and not error:
        this.setState({"sort_items": data, "loading": False})
    elif error:
        pass
    else:
        client.call_func("get_sort_indexes", this.get_items)
        this.setState({"loading": True})


def sortdropdown_change(e, d):
    if this.props.query:
        utils.go_to(this.props.history, query={'sort_idx': d.value}, push=False)
    if this.props.on_change:
        this.props.on_change(e, d)


def sortdropdown_render():
    item_options = []
    __pragma__("iconv")
    if this.state.sort_items:
        for x in sorted(this.state.sort_items, key=lambda k: k['name']):
            if x['item_type'] == this.props.item_type:
                item_options.append({
                    'value': x['index'],
                    'text': x['name'],
                    'icon': 'sort'
                })
    __pragma__("noiconv")
    return e(ui.Dropdown,
             placeholder=tr(this, "ui.t-sortdropdown-placeholder", "Sort by"),
             options=item_options,
             value=this.props.value,
             defaultValue=this.props.defaultValue,
             onChange=this.item_change,
             loading=this.state.loading,
             selectOnBlur=False,
             pointing=this.props.pointing,
             labeled=this.props.labeled,
             inline=this.props.inline,
             compact=this.props.compact,
             button=this.props.button,
             item=this.props.item if utils.defined(this.props.item) else True,
             selection=this.props.selection if utils.defined(this.props.selection) else True,
             basic=this.props.basic
             )


SortDropdown = createReactClass({
    'displayName': 'SortDropdown',

    'getInitialState': lambda: {'sort_items': None, 'loading': False},

    'item_change': sortdropdown_change,
    'get_items': sortdropdown_get,
    'componentDidMount': lambda: this.get_items(),

    'render': sortdropdown_render
})


def filterdropdown_get(data=None, error=None):
    if data is not None and not error:
        items = {}
        for d in data:
            items[d['name']] = d
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
    item_options = []
    __pragma__("iconv")
    if this.state.db_items:
        for d in sorted(this.state.db_items):
            item_options.append({'text': d, 'value': this.state.db_items[d]['id'], 'icon': "filter"})
    __pragma__("noiconv")
    return e(ui.Dropdown,
             placeholder=tr(this, "ui.t-filterdropdown-placeholder", "Filter"),
             options=item_options,
             search=True,
             allowAdditions=True,
             value=this.props.value or js_undefined,
             defaultValue=this.props.defaultValue,
             onChange=this.item_change,
             loading=this.state.loading,
             selectOnBlur=False,
             pointing=this.props.pointing,
             labeled=this.props.labeled,
             inline=this.props.inline,
             compact=this.props.compact,
             button=this.props.button,
             item=this.props.item if utils.defined(this.props.item) else True,
             selection=this.props.selection if utils.defined(this.props.selection) else True,
             basic=this.props.basic
             )


FilterDropdown = createReactClass({
    'displayName': 'FilterDropdown',

    'getInitialState': lambda: {'db_items': None, 'loading': False},

    'item_change': filterdropdown_change,
    'get_items': filterdropdown_get,
    'componentDidMount': lambda: this.get_items(),

    'render': filterdropdown_render
})


def viewdropdown_change(e, d):
    if this.props.query:
        utils.go_to(this.props.history, query={'view_type': d.value}, push=False)
    if this.props.on_change:
        this.props.on_change(e, d)


def viewdropdown_render():
    item_options = [
        {'text': tr(this, "ui.mi-all", "All"),
         'value': ViewType.All,
         },
        {'text': tr(this, "ui.mi-library", "Library"),
         'value': ViewType.Library,
         },
        {'text': tr(this, "ui.mi-inbox", "Inbox"),
         'value': ViewType.Inbox,
         },
    ]

    if this.props.view_type == ViewType.Favorite:
        item_options = [
            {'text': tr(this, "ui.mi-favorites", "Favorites"),
                'value': this.props.view_type,
             },
        ]
    elif this.props.view_type != None:  # noqa: E711
        for x in item_options:
            if x['value'] == this.props.view_type:
                item_options = [x]
                break

    return e(ui.Dropdown,
             options=item_options,
             value=this.props.value,
             defaultValue=this.props.defaultValue,
             onChange=this.item_change,
             selectOnBlur=False,
             pointing=this.props.pointing,
             labeled=this.props.labeled,
             inline=this.props.inline,
             compact=this.props.compact,
             button=this.props.button,
             item=this.props.item,
             selection=this.props.selection,
             basic=this.props.basic,
             className=this.props.className,
             disabled=True if this.props.view_type != None else js_undefined,  # noqa: E711
             icon=None if this.props.view_type else js_undefined
             )


ViewDropdown = createReactClass({
    'displayName': 'ViewDropdown',

    'item_change': viewdropdown_change,
    'render': viewdropdown_render
})
