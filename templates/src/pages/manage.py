from src.react_utils import (e,
                             h,
                             Route,
                             Redirect,
                             NavLink,
                             Switch,
                             createReactClass)
from src.ui import ui, Pagination, TitleChange, TR
from src.client import client, ItemType, ItemSort
from src.i18n import tr
from src.state import state
from src.propsviews import artistpropsview, tagpropsview, circlepropsview, parodypropsview
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')
__pragma__('alias', 'js_input', 'input')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


__pragma__("tconv")


def simplelayout_render():
    props = this.props
    stats_el = []
    if props.stats:
        stats_el.append(
            e(ui.Statistic.Group,
              *props.stats,
              size="mini",
              )
        )

    search_el = []
    if props.search:
        search_el.append(e(ui.Divider, hidden=True, section=True))
        search_el.append(
            e(ui.Search, placeholder=props.search_placeholder, fluid=True,
              js_input={'fluid': True},
              showNoResults=False,
              defaultValue=props.search_query,
              onSearchChange=props.search_change)
        )

    pages_el = []
    if props.pages:
        if props.item_count > props.limit:
            pages_el.append(
                e(ui.Grid.Row,
                    e(ui.Responsive,
                        e(Pagination,
                            limit=1,
                            pages=props.item_count / props.limit,
                            current_page=props.page,
                            on_change=props.set_page,
                            query=True,
                            scroll_top=True,
                            size="tiny"),
                        maxWidth=578,
                      ),
                    e(ui.Responsive,
                        e(Pagination,
                            pages=props.item_count / props.limit,
                            current_page=props.page,
                            on_change=props.set_page,
                            query=True,
                            scroll_top=True),
                        minWidth=579,
                      ),
                    centered=True
                  ),
            )

    return e(ui.Container,
             e(ui.Segment.Group,
               e(ui.Segment,
                 e(ui.Button, compact=True, basic=True,
                   icon="options", floated="right",
                   ),
                 e(ui.Button, e(ui.Icon, js_name="plus"), tr(this, "ui.b-new", "New"), compact=True, disabled=True, basic=True, floated="right",
                   ),
                 *stats_el,
                 *search_el,
                 clearing=True
                 ),
               e(ui.Segment,
                 e(ui.Grid,
                   *pages_el,
                   e(ui.Grid.Row,
                     e(ui.Grid.Column,
                       props.children,
                       width=16,
                       )
                     ),
                   *pages_el,
                   padded="horizontally",
                   ),
                 secondary=True, basic=True,
                 loading=props.loading)
               ))


__pragma__("notconv")

SimpleLayout = createReactClass({
    'displayName': 'SimpleLayout',
    'render': simplelayout_render
})

def scanpage_render():
    return e("div", e(TitleChange, title=tr(this, "ui.mi-scan", "Scan")),)


ScanPage = createReactClass({
    'displayName': 'ScanPage',

    'getInitialState': lambda: {
        'data': {},
    },

    'render': scanpage_render
})

def creategallery_render():
    return e("div",)


CreateGallery = createReactClass({
    'displayName': 'CreateGallery',

    'getInitialState': lambda: {
        'data': {},
    },

    'render': creategallery_render
})

def createcollection_render():
    return e("div",)


CreateCollection= createReactClass({
    'displayName': 'CreateCollection',

    'getInitialState': lambda: {
        'data': {},
    },

    'render': createcollection_render
})

def createpage_render():
    return e(ui.Container, 
             e(TitleChange, title=tr(this, "ui.mi-create", "Create")),
             e(ui.Button.Group,
               e(ui.Button, tr(this, "general.db-item-gallery", "Gallery"),
                 value=ItemType.Gallery,
                 active=this.state.item_type==ItemType.Gallery,
                 primary=this.state.item_type==ItemType.Gallery,
                 onClick=this.set_item_type,
                 ),
               e(ui.Button.Or, text=tr(this, "ui.t-or", "Or")),
               e(ui.Button, tr(this, "general.db-item-collection", "Collection"),
                 value=ItemType.Collection,
                 active=this.state.item_type==ItemType.Collection,
                 primary=this.state.item_type==ItemType.Collection,
                 onClick=this.set_item_type,
                 ),
               toggle=True,
               )
             )


CreatePage = createReactClass({
    'displayName': 'CreatePage',

    'getInitialState': lambda: {
        'data': {},
        'item_type': this.props.item_type or ItemType.Gallery,
    },
    'set_item_type': lambda e,d: this.setState({'item_type':d.value}),

    'render': createpage_render
})

Page = createReactClass({
    'displayName': 'ManagePage',

    'componentWillMount': lambda: this.props.menu([
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-create", "Create"), as_=NavLink,
          to="/manage/create", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-scan", "Scan"), as_=NavLink,
          to="/manage/scan", activeClassName="active"),
    ], pointing=True),

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Segment,
                        e(Switch,
                            e(Route, path="/manage/create", component=CreatePage),
                            e(Route, path="/manage/scan", component=ScanPage),
                            e(Redirect, js_from="/manage", exact=True, to={'pathname': "/manage/create"}),
                          ),
                        basic=True,
                        )
})

