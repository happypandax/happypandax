__pragma__('alias', 'as_', 'as')
from src.react_utils import (h,
                         e,
                         React,
                         createReactClass)
from src.ui import ui
from src.i18n import tr
from src.state import state
from src.client import ViewType
from src import items

def page_render():
    return e(items.ItemViewPage, view_type=ViewType.Favorite)

Page = createReactClass({
    'displayName': 'FavoritesPage',

    'render': page_render
})

