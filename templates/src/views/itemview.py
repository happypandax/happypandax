import math
from src.react_utils import (e,
                             createReactClass)
from src.ui import ui, Error, Pagination
from src.client import (client, ItemType)
from src.i18n import tr
from src.state import state
from src.single import (galleryitem, pageitem, groupingitem, collectionitem)
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def Itemviewvonfig_render():
    props = this.props
    cfg_suffix = props.suffix or ""
    infinite_scroll_cfg = "infinite_scroll"
    item_count_cfg = "item_count"
    external_viewer_cfg = "external_viewer"
    group_gallery_cfg = "group_gallery"
    blur_cfg = "blur"

    item_count_options = [
        {'key': 10, 'text': '10', 'value': 10},
        {'key': 20, 'text': '20', 'value': 20},
        {'key': 30, 'text': '30', 'value': 30},
        {'key': 40, 'text': '40', 'value': 40},
        {'key': 50, 'text': '50', 'value': 50},
        {'key': 75, 'text': '75', 'value': 75},
        {'key': 100, 'text': '100', 'value': 100},
        {'key': 125, 'text': '125', 'value': 125},
        {'key': 150, 'text': '150', 'value': 150},
        {'key': 200, 'text': '200', 'value': 200},
        {'key': 250, 'text': '250', 'value': 250},
        #{'key': 300, 'text': '300', 'value': 300},
        #{'key': 400, 'text': '400', 'value': 400},
        #{'key': 500, 'text': '500', 'value': 500},
    ]

    ext_viewer_el = []
    if utils.is_same_machine():
        ext_viewer_el.append(e(ui.Form.Field,
                               control=ui.Checkbox,
                               label=tr(this, "ui.t-open-external-viewer", "Open in external viewer"), toggle=True,
                               defaultChecked=utils.storage.get(external_viewer_cfg + cfg_suffix, False),
                               onChange=lambda e, d: all((props.on_external_viewer(e, d),
                                                          utils.storage.set(external_viewer_cfg + cfg_suffix, d.checked))),
                               ))

    grp_gallery_el = []
    if props.item_type in (ItemType.Gallery, ItemType.Grouping):
        grp_gallery_el.append(
            e(ui.Form.Field,
              control=ui.Checkbox,
              label=tr(this, "ui.t-group-galleries", "Group galleries"), toggle=True,
              defaultChecked=utils.storage.get(group_gallery_cfg + cfg_suffix, False),
              onChange=lambda e, d: all((props.on_group_gallery(e, d),
                                         utils.storage.set(group_gallery_cfg + cfg_suffix, d.checked))),
              ))

    return e(ui.Sidebar,
             e(ui.Form,
               *grp_gallery_el,
               e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "ui.t-infinite-scroll", "Infinite Scroll"), toggle=True,
                 defaultChecked=utils.storage.get(infinite_scroll_cfg + cfg_suffix, False),
                 onChange=lambda e, d: all(
                     (props.on_infinite_scroll(
                         e, d), utils.storage.set(
                         infinite_scroll_cfg + cfg_suffix, d.checked))),
                 ),
               e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "ui.t-blur", "Blur"), toggle=True,
                 defaultChecked=utils.storage.get(blur_cfg + cfg_suffix, False),
                 onChange=lambda e, d: all(
                   (props.on_blur(
                       e, d), utils.storage.set(
                       blur_cfg + cfg_suffix, d.checked))),
                 ),
                 *ext_viewer_el,
                 e(ui.Form.Select, options=item_count_options, label=tr(this, "ui.t-items-per-page", "Items per page"), inline=True,
                   defaultValue=utils.storage.get(item_count_cfg + cfg_suffix, props.default_item_count or 30),
                   onChange=lambda e, d: all(
                       (props.on_item_count(
                           e, d), utils.storage.set(
                           item_count_cfg + cfg_suffix, d.value))),
                   ),
                 e(ui.Form.Field, tr(this, "ui.b-close", "Close"), control=ui.Button),
                 onSubmit=props.on_close,
               ),
             as_=ui.Segment,
             size="small",
             basic=True,
             visible=props.visible,
             direction="right",
             animation="push",
             )


ItemViewConfig = createReactClass({
    'displayName': 'ItemViewConfig',
    'render': Itemviewvonfig_render
})


def itemviewbase_render():
    props = this.props
    pagination = []

    if props.show_pagination or not utils.defined(props.show_pagination):
        pagination.append(e(ui.Grid.Row,
                            e(ui.Responsive,
                              e(Pagination,
                                history=this.props.history,
                                location=this.props.location,
                                limit=1,
                                pages=props.item_count / props.limit,
                                current_page=props.page,
                                on_change=props.set_page,
                                context=this.props.context or this.state.context_node,
                                query=this.props.query,
                                scroll_top=True,
                                size="tiny"),
                                maxWidth=578,
                              ),
                            e(ui.Responsive,
                                e(Pagination,
                                  history=this.props.history,
                                  location=this.props.location,
                                  pages=props.item_count / props.limit,
                                  context=this.props.context or this.state.context_node,
                                  current_page=props.page,
                                  on_change=props.set_page,
                                  query=this.props.query,
                                  scroll_top=True),
                                minWidth=579,
                              ),
                            centered=True,
                            ))

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

    cfg_el = []

    if props.config_el:
        cfg_el.append(props.config_el)

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

    infinite_el = []
    if this.props.infinite_scroll:
        infinite_el.append(e(ui.Grid.Row,
                             e(ui.Visibility,
                               e(ui.Loader, active=props.loading_more if utils.defined(
                                   props.loading_more) else (props.infinite_scroll and props.loading)),
                               onTopVisible=this.props.on_load_more,
                               once=False,
                               ),))

    el = e(ui.Sidebar.Pushable,
           *cfg_el,
           e(ui.Sidebar.Pusher,
             e(ui.Grid,
               *count_el,
               *pagination,
               *[e(ui.Grid.Column, c, verticalAlign="middle",
                   computer=4, tablet=3, mobile=6,
                   largeScreen=lscreen, widescreen=wscreen) for c in els],
               *infinite_el,
               *pagination,
               *count_el,
               padded="vertically",
               centered=True,
               verticalAlign="middle",
               as_=ui.Transition.Group,
               animation='pulse',
               duration=800,
               ),
             as_=ui.Segment,
             basic=True,
             loading=props.loading if utils.defined(
                 props.loading_more) else (
                 props.loading and not props.infinite_scroll),
               className="no-padding-segment"
             ),
           )

    if props.secondary or props.tertiary or len(add_el):
        el = e(ui.Segment,
               *add_el,
               el,
               basic=True,
               secondary=props.secondary,
               tertiary=props.tertiary,
               )

    return e(ui.Ref, el, innerRef=this.get_context_node,)


ItemViewBase = createReactClass({
    'displayName': 'ItemViewBase',

    'getInitialState': lambda: {'context_node': None},

    'get_context_node': lambda n: this.setState({'context_node': n}),

    'render': itemviewbase_render
})


def get_items(data=None, error=None):
    if data is not None and not error:
        new_data = []
        if this.state.infinite_scroll and \
                this.state.prev_page and this.state.prev_page < this.state.page:
            new_data.extend(this.state['items'])
        new_data.extend(data)
        this.setState({"items": new_data,
                       'loading': False,
                       'loading_more': False})
    elif error:
        state.app.notif("Failed to fetch item type: {}".format(this.props.item_type), level="error")
    else:
        item = this.props.item_type
        func_kw = {'item_type': item,
                   'page': max(int(this.state.page) - 1, 0),
                   'limit': this.props.limit or this.state.limit}
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
            if not this.state.prev_page:
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


def get_more():
    pages = math.ceil(this.state.item_count / this.state.limit)
    if this.state.infinite_scroll and this.state.page < pages:
        next_page = int(this.state.page) + 1
        this.setState({'page': next_page,
                       'prev_page': this.state.page,
                       'loading_more': True})
        if this.props.history:
            utils.go_to(this.props.history, query={'page': next_page}, push=False)


def item_view_on_update(p_props, p_state):
    if p_props.item_type != this.props.item_type:
        this.get_element()
        this.setState({'items': []})

    if utils.defined(this.props.search_query) and (this.props.search_query != this.state.search_query):
        squery = this.props.search_query
        if not squery:
            squery = ''
        this.setState({'search_query': squery})

    if any((
        p_props.item_type != this.props.item_type,
        p_props.related_type != this.props.related_type,
        p_props.item_id != this.props.item_id,
        p_props.filter_id != this.props.filter_id,
        p_props.view_filter != this.props.view_filter,
        p_props.search_options != this.props.search_options,
        p_state.search_query != this.state.search_query,
        p_props.limit != this.props.limit,
        p_state.limit != this.state.limit,
    )):
        this.reset_page()
        this.get_items_count()

    if any((
        p_props.item_type != this.props.item_type,
        p_props.related_type != this.props.related_type,
        p_props.item_id != this.props.item_id,
        p_props.filter_id != this.props.filter_id,
        p_props.view_filter != this.props.view_filter,
        p_props.search_options != this.props.search_options,
        p_state.search_query != this.state.search_query,
        p_props.limit != this.props.limit,
        p_state.limit != this.state.limit,
        p_state.page != this.state.page,
        p_props.sort_by != this.props.sort_by,
        p_props.sort_desc != this.props.sort_desc,
    )):
        this.get_items()
        if not this.state.infinite_scroll:
            this.setState({'items': []})

    if any((
        p_props.sort_by != this.props.sort_by,
        p_props.sort_desc != this.props.sort_desc,
    )):
        this.reset_page()


def item_view_render():
    items = this.state['items']
    el = this.state.element
    limit = this.props.limit or this.state.limit
    size_type = this.props.size_type
    blur = this.state.blur
    if not el:
        return e(Error, content="An error occured. No valid element available.")
    ext_viewer = this.props.external_viewer if utils.defined(this.props.external_viewer) else this.state.external_viewer
    cfg_el = this.props.config_el or e(ItemViewConfig,
                                       item_type=this.props.related_type or this.props.item_type,
                                       on_close=this.props.toggle_config or this.toggle_config,
                                       visible=this.props.visible_config if utils.defined(
                                           this.props.visible_config) else this.state.visible_config,
                                       default_item_count=this.state.limit,
                                       on_infinite_scroll=this.on_infinite_scroll,
                                       suffix=this.props.config_suffix,
                                       on_item_count=this.on_item_count,
                                       on_external_viewer=this.on_external_viewer,
                                       on_group_gallery=this.on_group_gallery,
                                       on_blur=this.on_blur,
                                       )

    return e(ItemViewBase,
             [e(el, data=x, size_type=size_type, blur=blur, centered=True, className="medium-size", key=n, external_viewer=ext_viewer)
              for n, x in enumerate(items)],
             loading=this.state.loading,
             secondary=this.props.secondary,
             tertiary=this.props.tertiary,
             container=this.props.container,
             item_count=this.state.item_count,
             limit=limit,
             page=this.state.page,
             set_page=this.set_page,
             label=this.props.label,
             config_el=cfg_el,
             toggle_config=this.props.toggle_config,
             infinite_scroll=this.state.infinite_scroll,
             on_load_more=this.get_more,
             loading_more=this.state.loading_more,
             query=True,
             history=this.props.history,
             location=this.props.location,
             context=this.props.context,
             show_count=this.props.show_count,
             show_pagination=this.props.show_pagination,
             )


ItemView = createReactClass({
    'displayName': 'ItemView',

    'config_suffix': lambda: this.props.config_suffix or "",

    'getInitialState': lambda: {'page': 1,
                                'prev_page': 0,
                                'search_query': utils.get_query("search", "") or this.props.search_query,
                                'infinite_scroll': utils.storage.get("infinite_scroll" + this.config_suffix(), this.props.infinite_scroll),
                                'limit': utils.storage.get("item_count" + this.config_suffix(),
                                                           this.props.default_limit or (10 if this.props.related_type == ItemType.Page else 30)),
                                'items': [],
                                "element": None,
                                "loading": True,
                                "loading_more": False,
                                'item_count': 1,
                                'visible_config': False,
                                'external_viewer': utils.storage.get("external_viewer" + this.config_suffix(), False),
                                'group_gallery': utils.storage.get("group_gallery" + this.config_suffix(), False),
                                'blur': utils.storage.get("blur" + this.config_suffix(), False),
                                },

    'get_items_count': get_items_count,
    'get_items': get_items,
    'get_element': get_element,
    'get_more': get_more,

    'reset_page': lambda p: all((this.setState({'page': 1}), utils.go_to(this.props.history, query={'page': 1}, push=False))),
    'set_page': lambda p: this.setState({'page': p, 'prev_page': None}),

    'on_blur': lambda e, d: this.setState({'blur': d.checked}),
    'on_infinite_scroll': lambda e, d: this.setState({'infinite_scroll': d.checked}),
    'on_item_count': lambda e, d: this.setState({'limit': d.value}),
    'on_external_viewer': lambda e, d: this.setState({'external_viewer': d.checked}),
    'on_group_gallery': lambda e, d: this.setState({'group_gallery': d.checked}),
    'toggle_config': lambda a: this.setState({'visible_config': not this.state.visible_config}),

    'componentWillMount': lambda: this.get_element(),
    'componentDidMount': lambda: all((this.get_items(), this.get_items_count())),
    'componentDidUpdate': item_view_on_update,

    'render': item_view_render
})


def simpleview_render():
    return e("div",
             this.props.children,
             e(ui.Visibility,
               e(ui.Segment,
                 e(ui.Loader, active=this.props.loading),
                 basic=True,
                 ),
               onTopVisible=this.props.on_load_more,
               once=False,
               context=this.props.context or this.state.ref,
               ),
             ref=this.get_ref
             )


SimpleView = createReactClass({
    'displayName': 'SimpleCardView',

    'getInitialState': lambda: {'ref': None},

    'get_ref': lambda r: this.setState({'ref': r}),

    'render': simpleview_render
})
