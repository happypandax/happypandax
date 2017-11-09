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
    return e(items.ItemViewPage, view_type=ViewType.Library)

Page = createReactClass({
    'displayName': 'LibraryPage',

    'render': page_render
})

