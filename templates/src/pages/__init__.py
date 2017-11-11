__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             withRouter)
from src.ui import ui
from src.client import ItemType
from src.i18n import tr
from src.state import state
from src.views import itemview
from src import utils, item

__pragma__("kwargs")
def item_view_menu(on_item_change=None, on_filter_change=None, default_item=None, on_search=None, default_filter=None):
    return [e(ui.Menu.Item, e(withRouter(item.ItemDropdown), on_change=on_item_change, value=default_item, query=True), fitted=True),
            e(ui.Menu.Menu,
                e(ui.Menu.Item,
                    e(withRouter(item.Search), size="small", fluid=True, className="fullwidth", on_search=on_search, query=True), className="fullwidth",),
                position="left",
                className="fullwidth"),
            e(ui.Menu.Item, e(ui.Icon, js_name="sort"), e(item.SortDropdown, on_change=None, value=None), fitted=True),
            e(ui.Menu.Item, e(ui.Icon, js_name="filter"), e(withRouter(item.FilterDropdown),
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
    return e(itemview.ItemView,
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
