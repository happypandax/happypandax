__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass)
from ui import ui
from i18n import tr
from client import ViewType
from state import state
import items

def page_render():
    return e(items.ItemView,
                        item_type=this.state.item_type,
                        view_filter=ViewType.Inbox)

Page = createReactClass({
    'displayName': 'InboxPage',

    'componentWillMount': lambda: this.props.menu(items.item_view_menu()),

    'getInitialState': lambda: {'item_type':items.ItemType.Gallery},

    'render': page_render
})

