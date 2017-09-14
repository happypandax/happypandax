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
                        view_filter=ViewType.Favorite)

Page = createReactClass({
    'displayName': 'FavoritesPage',

    'componentWillMount': lambda: this.props.menu([
                    e(ui.Menu.Menu,
                    e(ui.Menu.Item,
                     e(items.Search, size="small", fluid=True, className="fullwidth"), className="fullwidth"),
                    position="left",
                    className="fullwidth"),
                    e(ui.Popup,
                      e(ui.Grid, centered=True),
                      trigger=e(ui.Menu.Item, e(ui.Icon, js_name="options"), "View Options",),
                      hoverable=True,
                      on="click",
                      flowing=True,
                      ),
                    ]),

    'getInitialState': lambda: {'item_type':items.ItemType.Gallery},

    'render': page_render
})

