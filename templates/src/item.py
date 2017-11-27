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
    if this.state.sort_items:
        for i in this.state.sort_items:
            item_options.append({
                'value':i['index'],
                'text':i['name'],
                })
    return e(ui.Dropdown,
             placeholder="Sort by",
             selection=True, item=True,
             options=item_options,
             value=this.props.value if this.props.value else js_undefined,
             defaultValue=this.props.defaultValue,
             onChange=this.item_change,
             loading=this.state.loading
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
