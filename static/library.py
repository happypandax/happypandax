__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass)
from ui import ui
from i18n import tr
from state import state
from client import ViewType
import items

def page_render():
    return e(items.ItemView,
                        item_type=this.state.item_type,
                        view_filter=ViewType.Library,
                        search_query=this.state.search_query)

Page = createReactClass({
    'displayName': 'LibraryPage',

    'on_item_change': lambda e, d: this.setState({'item_type':d.value}),

    'on_search': lambda e, d: this.setState({'search_query':d.value}),

    'componentWillMount': lambda: this.props.menu(
        items.item_view_menu(
            on_item_change=this.on_item_change,
            default_item=this.state.item_type,
            on_search=this.on_search,
            )),

    'getInitialState': lambda: {'item_type':items.ItemType.Gallery,
                                'search_query':""},

    'render': page_render
})

