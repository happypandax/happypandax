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
                        view_filter=ViewType.Library)

Page = createReactClass({
    'displayName': 'LibraryPage',

    'componentWillMount': lambda: this.props.menu(items.item_view_menu()),

    'getInitialState': lambda: {'item_type':items.ItemType.Grouping},

    'render': page_render
})

