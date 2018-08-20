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


def get_db_status(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
    elif error:
        state.app.notif("Failed to fetch status", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("get_items", this.get_items,
                         item_type=ItemType.Status)
        this.setState({'data_loading': True})


__pragma__("tconv")


def statuspage_render():

    items = []

    for item in sorted(this.state.data, key=lambda x: x['name'].lower()):
        items.append(
            e(ui.Card,
                e(ui.Card.Content, e(ui.Card.Description, item['name'])),
              centered=True,
              link=True,
              className="default-card",
              key=item.id)
        )

    return e(SimpleLayout,
             e(TitleChange, title=tr(this, "ui.mi-dir-status", "Status")),
             e(ui.Card.Group, items, itemsPerRow=1, doubling=True, stackable=True,
               as_=ui.Transition.Group,
               animation="scale",
               duration=500,),
             loading=this.state.data_loading,
             )


__pragma__("notconv")

StatusPage = createReactClass({
    'displayName': 'StatusPage',

    'getInitialState': lambda: {
        'data': [],
        'data_loading': False,
    },

    'get_items': get_db_status,

    'componentDidMount': lambda: all((this.get_items(),)),

    'render': statuspage_render
})


def get_db_languages(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
    elif error:
        state.app.notif("Failed to fetch languages", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("get_items", this.get_items,
                         item_type=ItemType.Language)
        this.setState({'data_loading': True})


__pragma__("tconv")


def languagespage_render():

    items = []

    for item in sorted(this.state.data, key=lambda x: x['name'].lower()):
        items.append(
            e(ui.Card,
                e(ui.Card.Content, e(ui.Card.Description, item['name'])),
              centered=True,
              link=True,
              className="default-card",
              key=item.id)
        )

    return e(SimpleLayout,
             e(TitleChange, title=tr(this, "ui.mi-dir-languages", "Languages")),
             e(ui.Card.Group, items, itemsPerRow=1, doubling=True, stackable=True,
               as_=ui.Transition.Group,
               animation="scale",
               duration=500,),
             loading=this.state.data_loading,
             )


__pragma__("notconv")

LanguagesPage = createReactClass({
    'displayName': 'LanguagesPage',

    'getInitialState': lambda: {
        'data': [],
        'data_loading': False,
    },

    'get_items': get_db_languages,

    'componentDidMount': lambda: all((this.get_items(),)),

    'render': languagespage_render
})


def get_db_parodies(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
        this.get_items_count()
    elif error:
        state.app.notif("Failed to fetch parodies", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("search_items", this.get_items,
                         item_type=ItemType.Parody,
                         search_query=this.state.search_query,
                         sort_by=ItemSort.ParodyName,
                         offset=this.state.limit * (this.state.page - 1),
                         limit=this.state.limit)
        this.setState({'data_loading': True})


def get_parodies_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"count": data['count']})
    elif error:
        state.app.notif("Failed to fetch parody count", level="error")
    else:
        client.call_func("get_count", this.get_items_count, item_type=ItemType.Parody)


__pragma__("tconv")


def parodiespage_render():

    items = []

    unk = tr(this, "ui.t-bracket-unknown", "<Unknown>")
    for parody in this.state.data:
        aname = unk
        if parody.names:
            aname = parody.names[0]['name']
        items.append(
            e(ui.Popup,
                e(parodypropsview.ParodyProps, data=parody),
              trigger=e(ui.Card,
                        e(ui.Card.Content, e(ui.Card.Description, aname)),
                        centered=True, link=True, className="default-card"),
              hoverable=True,
              wide="very",
              on="click",
              hideOnScroll=True,
              position="top center",
              key=parody.id
              )
        )

    return e(SimpleLayout,
             e(TitleChange, title=tr(this, "ui.mi-dir-parodies", "Parodies")),
             e(ui.Card.Group, items, itemsPerRow=1, doubling=True, stackable=True,
               as_=ui.Transition.Group,
               animation="scale",
               duration=500,),
             loading=this.state.data_loading,
             pages=True,
             item_count=this.state.count,
             limit=this.state.limit,
             page=this.state.page,
             set_page=this.set_page,
             search=True,
             search_query=this.state.search_query,
             search_change=this.update_search,
             search_placeholder=tr(this, "ui.t-search-parodies-placeholder", "Search parodies"),
             stats=[e(ui.Statistic,
                      e(ui.Statistic.Value, this.state.count),
                      e(ui.Statistic.Label, tr(this, "ui.t-total-parodies", "Total parodies"))
                      )]
             )


__pragma__("notconv")


ParodiesPage = createReactClass({
    'displayName': 'ParodiesPage',

    'getInitialState': lambda: {
        'search_query': utils.get_query("search", "") or this.props.search_query,
        'data': [],
        'limit': 50,
        'page': 1,
        'count': 0,
        'data_loading': False,
    },

    'get_items': get_db_parodies,
    'get_items_count': get_parodies_count,
    'set_page': lambda p: all((this.setState({'page': p}), )),

    'update_search': lambda e, d: all((this.setState({'search_query': d.value}),
                                       utils.go_to(this.props.history, query={'search': d.value}, push=False))),

    'componentDidMount': lambda: all((this.get_items(), this.get_items_count())),

    'componentDidUpdate': lambda p_p, p_s: this.get_items() if any((p_s.search_query != this.state.search_query,
                                                                    p_s.page != this.state.page)) else None,

    'render': parodiespage_render
})


def get_db_categories(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
    elif error:
        state.app.notif("Failed to fetch categories", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("get_items", this.get_items,
                         item_type=ItemType.Category)
        this.setState({'data_loading': True})


__pragma__("tconv")


def categorypage_render():

    items = []

    for cat in sorted(this.state.data, key=lambda x: x['name'].lower()):
        items.append(
            e(ui.Card,
                e(ui.Card.Content, e(ui.Card.Description, cat['name'])),
              centered=True,
              link=True,
              className="default-card",
              key=cat.id)
        )

    return e(SimpleLayout,
             e(TitleChange, title=tr(this, "ui.mi-dir-categories", "Categories")),
             e(ui.Card.Group, items, itemsPerRow=1, doubling=True, stackable=True,
               as_=ui.Transition.Group,
               animation="scale",
               duration=500,),
             loading=this.state.data_loading,
             )


__pragma__("notconv")

CategoriesPage = createReactClass({
    'displayName': 'CategoriesPage',

    'getInitialState': lambda: {
        'data': [],
        'data_loading': False,
    },

    'get_items': get_db_categories,

    'componentDidMount': lambda: all((this.get_items(),)),

    'render': categorypage_render
})


def get_db_circles(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
    elif error:
        state.app.notif("Failed to fetch circles", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("search_items", this.get_items,
                         item_type=ItemType.Circle,
                         search_query=this.state.search_query,
                         sort_by=ItemSort.CircleName,
                         offset=this.state.limit * (this.state.page - 1),
                         limit=this.state.limit)
        this.setState({'data_loading': True})


def get_circles_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"count": data['count']})
    elif error:
        state.app.notif("Failed to fetch circle count", level="error")
    else:
        client.call_func("get_count", this.get_items_count, item_type=ItemType.Circle)


__pragma__("tconv")


def circlespage_render():

    items = []

    for item in sorted(this.state.data, key=lambda x: x['name'].lower()):
        items.append(
            e(ui.Popup,
              e(circlepropsview.CircleProps, data=item),
              trigger=e(ui.Card,
                        e(ui.Card.Content, e(ui.Card.Description, item['name']),
                          ),
                        centered=True, link=True, className="default-card"),
              hoverable=True,
              wide="very",
              on="click",
              hideOnScroll=True,
              position="top center",
              key=item.id,
              )
        )

    return e(SimpleLayout,
             e(TitleChange, title=tr(this, "ui.mi-dir-circles", "Circles")),
             e(ui.Card.Group, items, itemsPerRow=2, doubling=True, stackable=True,
               as_=ui.Transition.Group,
               animation="scale",
               duration=500,),
             loading=this.state.data_loading,
             pages=True,
             item_count=this.state.count,
             limit=this.state.limit,
             page=this.state.page,
             set_page=this.set_page,
             search=True,
             search_query=this.state.search_query,
             search_change=this.update_search,
             search_placeholder=tr(this, "ui.t-search-circles-placeholder", "Search cricles"),
             stats=[e(ui.Statistic,
                      e(ui.Statistic.Value, this.state.count),
                      e(ui.Statistic.Label, tr(this, "ui.t-total-circles", "Total circles"))
                      )]
             )


__pragma__("notconv")

CirclesPage = createReactClass({
    'displayName': 'CirclesPage',

    'getInitialState': lambda: {
        'search_query': utils.get_query("search", "") or this.props.search_query,
        'data': [],
        'limit': 50,
        'page': 1,
        'count': 0,
        'data_loading': False,
    },

    'get_items': get_db_circles,
    'get_items_count': get_circles_count,
    'set_page': lambda p: all((this.setState({'page': p}), )),

    'update_search': lambda e, d: all((this.setState({'search_query': d.value}),
                                       utils.go_to(this.props.history, query={'search': d.value}, push=False))),

    'componentDidMount': lambda: all((this.get_items(), this.get_items_count())),

    'componentDidUpdate': lambda p_p, p_s: this.get_items() if any((p_s.search_query != this.state.search_query,
                                                                    p_s.page != this.state.page)) else None,

    'render': circlespage_render
})


def get_db_artists(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
        this.get_items_count()
    elif error:
        state.app.notif("Failed to fetch artists", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("search_items", this.get_items,
                         item_type=ItemType.Artist,
                         search_query=this.state.search_query,
                         sort_by=ItemSort.ArtistName,
                         offset=this.state.limit * (this.state.page - 1),
                         limit=this.state.limit)
        this.setState({'data_loading': True})


def get_artists_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"count": data['count']})
    elif error:
        state.app.notif("Failed to fetch artist count", level="error")
    else:
        client.call_func("get_count", this.get_items_count, item_type=ItemType.Artist)


__pragma__("tconv")


def artistpage_render():

    items = []
    unk = tr(this, "ui.t-bracket-unknown", "<Unknown>")
    for artist in this.state.data:
        aname = unk
        if artist.names:
            aname = artist.names[0]['name']
        items.append(
            e(ui.Modal,
              e(ui.Modal.Content,
                e(artistpropsview.ArtistProps, data=artist),
                ),
                trigger=e(ui.Card, e(ui.Card.Content, e(ui.Card.Description, aname)),
                          centered=True, link=True, className="default-card"),
                dimmer="inverted",
                size="small",
                closeOnDocumentClick=True,
                closeIcon=True,
                key=artist.id,
              )
        )
    return e(SimpleLayout,
             e(TitleChange, title=tr(this, "ui.mi-dir-artists", "Artists")),
             e(ui.Card.Group, items, itemsPerRow=2, doubling=True, stackable=True,
               as_=ui.Transition.Group,
               animation="scale",
               duration=500,),
             loading=this.state.data_loading,
             pages=True,
             item_count=this.state.count,
             limit=this.state.limit,
             page=this.state.page,
             set_page=this.set_page,
             search=True,
             search_query=this.state.search_query,
             search_change=this.update_search,
             search_placeholder=tr(this, "ui.t-search-artists-placeholder", "Search artists"),
             stats=[e(ui.Statistic,
                      e(ui.Statistic.Value, this.state.count),
                      e(ui.Statistic.Label, tr(this, "ui.t-total-artists", "Total artists"))
                      )]
             )


__pragma__("notconv")


ArtistsPage = createReactClass({
    'displayName': 'ArtistsPage',

    'getInitialState': lambda: {
        'search_query': utils.get_query("search", "") or this.props.search_query,
        'data': [],
        'limit': 50,
        'page': utils.get_query("page", 1),
        'count': 0,
        'data_loading': False,
    },

    'get_items': get_db_artists,
    'get_items_count': get_artists_count,
    'set_page': lambda p: all((this.setState({'page': p}), )),

    'update_search': lambda e, d: all((this.setState({'search_query': d.value, 'page': 1}),
                                       utils.go_to(this.props.history, query={'search': d.value}, push=False))),

    'componentDidMount': lambda: all((this.get_items(), this.get_items_count())),

    'componentDidUpdate': lambda p_p, p_s: this.get_items() if any((p_s.search_query != this.state.search_query,
                                                                    p_s.page != this.state.page)) else None,

    'render': artistpage_render
})


def get_db_tags(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
        this.get_tags_count()
    elif error:
        state.app.notif("Failed to fetch tags", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("search_tags", this.get_tags,
                         search_query=this.state.search_query,
                         sort_by=ItemSort.NamespaceTagTag,
                         offset=this.state.limit * (this.state.page - 1),
                         limit=this.state.limit)
        this.setState({'data_loading': True})


def get_tags_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"count": data['count']})
    elif error:
        state.app.notif("Failed to fetch tags count", level="error")
    else:
        client.call_func("get_tags_count", this.get_tags_count)


def tagspage_update(p_p, p_s):
    if any((
        p_s.search_query != this.state.search_query,
        p_s.page != this.state.page
    )):
        this.get_tags()


def tagspage_render():

    tag_lbl = []

    nstags = this.state.data

    if nstags.__namespace__:  # somehow transcrypt ignores this in the loop below
        for t in sorted(nstags.__namespace__, key=lambda x: x.js_name):
            tag_lbl.append(
                e(ui.Modal,
                  e(ui.Modal.Content,
                    e(tagpropsview.TagProps, tag=t.js_name, namespace=""),
                    ),
                    trigger=e(ui.Card,
                              e(ui.Card.Content, e(ui.Card.Description, t.js_name)),
                              centered=True, link=True, className="default-card"),
                    dimmer="inverted",
                    size="small",
                    closeOnDocumentClick=True,
                    closeIcon=True,
                    key=t.id,
                  ))

    for ns in sorted(dict(nstags).keys()):
        for t in sorted(nstags[ns], key=lambda x: x.js_name):
            tag_lbl.append(
                e(ui.Modal,
                  e(ui.Modal.Content,
                    e(tagpropsview.TagProps, tag=t.js_name, namespace=ns),
                    ),
                    trigger=e(ui.Card,
                              e(ui.Card.Content,
                                e(ui.Card.Description, h("span", ns + ':', className="sub-text"), t.js_name)),
                              centered=True, link=True, className="default-card"),
                    dimmer="inverted",
                    size="small",
                    closeOnDocumentClick=True,
                    closeIcon=True,
                    key=t.id,
                  ))

    return e(SimpleLayout,
             e(TitleChange, title=tr(this, "ui.mi-dir-tags", "Tags")),
             e(ui.Card.Group, tag_lbl, itemsPerRow=4, doubling=True, stackable=True,
               as_=ui.Transition.Group,
               animation="scale",
               duration=500,),
             loading=this.state.data_loading,
             pages=True,
             item_count=this.state.count,
             limit=this.state.limit,
             page=this.state.page,
             set_page=this.set_page,
             search=True,
             search_query=this.state.search_query,
             search_change=this.update_search,
             search_placeholder=tr(this, "ui.t-search-tags-placeholder", "Search tags"),
             stats=[e(ui.Statistic,
                      e(ui.Statistic.Value, this.state.count),
                      e(ui.Statistic.Label, tr(this, "ui.t-total-tags", "Total Tags"))
                      )]
             )


TagsPage = createReactClass({
    'displayName': 'TagsPage',

    'getInitialState': lambda: {
        'search_query': utils.get_query("search", "") or this.props.search_query,
        'data': {},
        'limit': 50,
        'page': utils.get_query("page", 1),
        'count': 0,
        'data_loading': False,
    },

    'get_tags': get_db_tags,
    'get_tags_count': get_tags_count,
    'set_page': lambda p: all((this.setState({'page': p}), )),

    'update_search': lambda e, d: all((this.setState({'search_query': d.value, 'page': 1}),
                                       utils.go_to(this.props.history, query={'search': d.value}, push=False))),

    'componentDidMount': lambda: all((this.get_tags(), this.get_tags_count())),

    'componentDidUpdate': tagspage_update,

    'render': tagspage_render
})

Page = createReactClass({
    'displayName': 'DirectoryPage',

    'componentWillMount': lambda: this.props.menu([
        e(ui.Menu.Item, e(TR, "ui.mi-dir-tags", default="Tags"), as_=NavLink,
          to="/directory/tags", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-dir-artists", "Artists"), as_=NavLink,
          to="/directory/artists", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-dir-circles", "Circles"), as_=NavLink,
          to="/directory/circles", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-dir-categories", "Categories"), as_=NavLink,
          to="/directory/categories", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-dir-parodies", "Parodies"), as_=NavLink,
          to="/directory/parodies", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-dir-languages", "Languages"), as_=NavLink,
          to="/directory/languages", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-dir-status", "Status"), as_=NavLink,
          to="/directory/status", activeClassName="active"),
    ], pointing=True),

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Segment,
                        e(Switch,
                            e(Route, path="/directory/tags", component=TagsPage),
                            e(Route, path="/directory/artists", component=ArtistsPage),
                            e(Route, path="/directory/circles", component=CirclesPage),
                            e(Route, path="/directory/categories", component=CategoriesPage),
                            e(Route, path="/directory/parodies", component=ParodiesPage),
                            e(Route, path="/directory/languages", component=LanguagesPage),
                            e(Route, path="/directory/status", component=StatusPage),
                            e(Redirect, js_from="/directory", exact=True, to={'pathname': "/directory/tags"}),
                          ),
                        basic=True,
                        )
})
