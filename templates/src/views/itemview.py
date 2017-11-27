__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
from src.ui import ui, Error, Pagination
from src.client import (client, ItemType)
from src.i18n import tr
from src.state import state
from src.single import (galleryitem, pageitem, groupingitem, collectionitem)
from src import utils

def ItemViewConfig(props):
    item_count_options = [
        {'key':10, 'text':'10', 'value':10},
        {'key':20, 'text':'20', 'value':20},
        {'key':30, 'text':'30', 'value':30},
        {'key':40, 'text':'40', 'value':40},
        {'key':50, 'text':'50', 'value':50},
        {'key':75, 'text':'75', 'value':75},
        {'key':100, 'text':'100', 'value':100},
        {'key':125, 'text':'125', 'value':125},
        {'key':150, 'text':'150', 'value':150},
        {'key':200, 'text':'200', 'value':200},
        ]

    ext_viewer_el = []
    if utils.is_same_machine():
        ext_viewer_el.append(e(ui.Form.Field, control=ui.Checkbox, label="Open in external viewer", toggle=True))

    return e(ui.Transition,
            e(ui.Container,
              e(ui.Form,
                e(ui.Form.Group,
                    e(ui.Form.Field, control=ui.Checkbox, label="Infinite Scroll", toggle=True),
                    *ext_viewer_el,
                  ),
                e(ui.Form.Group,
                    e(ui.Form.Select, options=item_count_options, label="Item Count", inline=True),
                  ),
                e(ui.Form.Field, "Close", control=ui.Button),
                onSubmit=props.onSubmit,
                ),
              as_=ui.Segment,
            size="tiny",
            compact=True,
            ),
            visible=props.visible,
            animation="scale",
            duration=200,
            unmountOnHide=True, #props.unmountOnHide,
            )

def itemviewbase_render():
    props = this.props
    pagination = e(ui.Grid.Row,
                   e(ui.Responsive,
                       e(Pagination,
                         limit=1,
                         pages=props.item_count / props.limit,
                         current_page=props.page,
                         on_change=props.set_page,
                         context=this.props.context,
                         query=True,
                         scroll_top=True,
                         size="tiny"),
                       maxWidth=578,
                     ),
                   e(ui.Responsive,
                       e(Pagination,
                         pages=props.item_count / props.limit,
                         context=this.props.context,
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
        add_el.append(e(ui.Label,
                        props.label,
                        e(ui.Label.Detail, props.item_count),
                        e(ui.Button, compact=True, basic=True,
                          icon="options", floated="right",
                          size="mini", onClick=props.toggle_config),
                        attached="top"))

    if props.config_el:
        add_el.append(props.config_el)

    count_el = []

    if (not utils.defined(props.show_count)) or props.show_count:
        count_el.append(e(ui.Grid.Column,
                          e(ui.Header,
                            e(ui.Header.Subheader,
                              tr(this,
                                  "ui.t-showing-count",
                                  "Showing {}".format(props.item_count),
                                 placeholder={
                                      'from': (
                                          props.page -
                                          1) *
                                      props.limit +
                                      1,
                                      'to': (
                                          props.page -
                                          1) *
                                      props.limit +
                                      len(els),
                                      'all': props.item_count}
                                 ),
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
        if this.props.sort_by:
            func_kw['sort_by'] = this.props.sort_by
        if this.props.sort_desc:
            func_kw['sort_desc'] = this.props.sort_desc
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
        ItemType.Gallery: galleryitem.Gallery,
        ItemType.Collection: collectionitem.Collection,
        ItemType.Grouping: groupingitem.Grouping,
        ItemType.Page: pageitem.Page,
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
        p_props.sort_by != this.props.sort_by,
        p_props.sort_desc != this.props.sort_desc,
    )):
        this.get_items()

    if any((
        p_props.sort_by != this.props.sort_by,
        p_props.sort_desc != this.props.sort_desc,
    )):
        this.setState({'page': 1})


def item_view_render():
    items = this.state['items']
    el = this.state.element
    limit = this.props.limit or this.state.default_limit
    if not el:
        return e(Error, content="An error occured")

    ext_viewer = this.props.external_viewer

    return e(ItemViewBase,
             [e(el, data=x, className="medium-size", key=n, external_viewer=ext_viewer) for n, x in enumerate(items)],
             loading=this.state.loading,
             secondary=this.props.secondary,
             tertiary=this.props.tertiary,
             container=this.props.container,
             item_count=this.state.item_count,
             limit=limit,
             page=this.state.page,
             set_page=this.set_page,
             label=this.props.label,
             config_el=this.props.config_el,
             toggle_config=this.props.toggle_config,
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
