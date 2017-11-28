__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             withRouter)
from src.ui import ui, ToggleIcon
from src.client import ItemType
from src.i18n import tr
from src.state import state
from src.views import itemview
from src import utils, item

__pragma__("kwargs")


def item_view_menu(history,
                    on_item_change=None,
                   default_item=None,
                   on_sort_change=None,
                   default_sort=None,
                   on_sort_desc=None,
                   default_sort_desc=None,
                   on_search=None,
                   on_filter_change=None,
                   default_filter=None,
                   on_toggle_config=None):
    return [e(ui.Menu.Item, e(item.ItemDropdown, history=history, on_change=on_item_change, value=default_item, query=True), fitted=True),
            e(ui.Menu.Menu,
                e(ui.Menu.Item,
                    e(withRouter(item.Search), size="small", fluid=True, className="fullwidth", on_search=on_search, query=True), className="fullwidth",),
                position="left",
                className="fullwidth"),
            e(ui.Menu.Item,
              e(ToggleIcon, icons=["sort content ascending", "sort content descending"],
                on_toggle=lambda a: all((
                    on_sort_desc(a),
                    utils.go_to(history, query={'sort_desc': int(a)}, push=False))),
                toggled=default_sort_desc,
                ),
              e(item.SortDropdown,
                history=history,
                on_change=on_sort_change, defaultValue=default_sort,
                item_type=default_item,
                query=True), fitted=True),
            e(ui.Menu.Item,
              e(ui.Icon, js_name="delete" if default_filter else "filter",
                link=True if default_filter else False,
                onClick=js_undefined if not default_filter else lambda: all((
                    on_filter_change(None, 0),
                    utils.go_to(history, query={'filter_id': 0}, push=False))),
                ),
              e(item.FilterDropdown,
                history=history,
                on_change=on_filter_change, value=default_filter,
                query=True), fitted=True),
            e(ui.Menu.Item, e(ui.Icon, js_name="options", size="large"), icon=True, onClick=on_toggle_config),
            ]
__pragma__("nokwargs")


def itemviewpage_update(p_p, p_s):
    if any((
        p_p.view_type != this.props.view_type,
        p_s.item_type != this.state.item_type,
        p_s.filter_id != this.state.filter_id,
    )):
        this.update_menu()


def itemviewpage_render():
    cfg_el = e(itemview.ItemViewConfig, onSubmit=this.toggle_config, visible=this.state.visible_config)

    return e(itemview.ItemView,
             item_type=this.state.item_type,
             view_filter=this.props.view_type,
             search_query=this.state.search_query,
             filter_id=this.state.filter_id,
             search_options=this.state.search_options,
             sort_by=this.state.sort_idx,
             sort_desc=this.state.sort_desc,
             config_el=cfg_el,
             )

ItemViewPage = createReactClass({
    'displayName': 'ItemViewPage',

    'toggle_config': lambda a: this.setState({'visible_config': not this.state.visible_config}),

    'on_item_change': lambda e, d: this.setState({'item_type': d.value}),

    'on_sort_change': lambda e, d: this.setState({'sort_idx': d.value}),

    'toggle_sort_desc': lambda d: this.setState({'sort_desc': not this.state.sort_desc}),

    'on_filter_change': lambda e, d: this.setState({'filter_id': d.value}),

    'on_search': lambda s, o: this.setState({'search_query': s, 'search_options': o}),

    'update_menu': lambda: state.app.set_menu_contents(
        item_view_menu(
            this.props.history,
            on_item_change=this.on_item_change,
            on_sort_change=this.on_sort_change,
            on_sort_desc=this.toggle_sort_desc,
            on_filter_change=this.on_filter_change,
            default_item=this.state.item_type,
            default_sort=this.state.sort_idx,
            default_sort_desc=this.state.sort_desc,
            default_filter=this.state.filter_id,
            on_search=this.on_search,
            on_toggle_config=this.toggle_config,
        )),

    'componentWillMount': lambda: this.update_menu(),

    'componentDidUpdate': itemviewpage_update,

    'getInitialState': lambda: {'item_type': int(utils.get_query("item_type", ItemType.Gallery)),
                                'filter_id': int(utils.get_query("filter_id", 0)),
                                'sort_idx': int(utils.get_query("sort_idx", 0)),
                                'sort_desc': bool(utils.get_query("sort_desc", 0)),
                                'search_query': "",
                                'search_options': {},
                                'visible_config': False,
                                },

    'render': itemviewpage_render
})
