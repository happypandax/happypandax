__pragma__('alias', 'as_', 'as')
__pragma__('alias', 'js_input', 'input')
from src.react_utils import (e,
                             Route,
                             Redirect,
                             NavLink,
                             Switch,
                             createReactClass)
from src.ui import ui
from src.client import client, ItemType
from src.i18n import tr
from src.state import state
from src.single import tagitem


def artistpage_render():
    return e(ui.Container,
             e(ui.Segment.Group,
               e(ui.Segment,
                 e(ui.Button, compact=True, basic=True,
                   icon="options", floated="right",
                   ),
                 e(ui.Divider, hidden=True, section=True),
                 e(ui.Search, placeholder=tr(this, "", "Search artists"), fluid=True,
                   js_input={'fluid': True}),
                 clearing=True,
                 ),
               e(ui.Segment, secondary=True, basic=True)
               ))


ArtistsPage = createReactClass({
    'displayName': 'ArtistsPage',

    'getInitialState': lambda: {},

    'render': artistpage_render
})


def get_db_tags(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data, 'data_loading': False})
    elif error:
        state.app.notif("Failed to fetch tags", level="error")
        this.setState({'data_loading': False})
    else:
        client.call_func("get_all_tags", this.get_tags, limit=25)
        this.setState({'data_loading': True})


def tagspage_render():

    tag_lbl = []

    nstags = this.state.data

    if nstags.__namespace__:  # somehow transcrypt ignores this in the loop below
        tags = sorted([x.js_name for x in nstags.__namespace__])
        for t in tags:
            tag_lbl.append(e(tagitem.TagLabel, tag=t))

    for ns in sorted(dict(nstags).keys()):
        tags = [x.js_name for x in nstags[ns]]
        for t in sorted(tags):
            tag_lbl.append(e(tagitem.TagLabel, namespace=ns, tag=t, show_ns=True))

    return e(ui.Container,
             e(ui.Segment.Group,
               e(ui.Segment,
                 e(ui.Button, compact=True, basic=True,
                   icon="options", floated="right",
                   ),
                 # e(ui.Statistic.Group,
                 #  e(ui.Statistic,
                 #    e(ui.Statistic.Value, 0),
                 #    e(ui.Statistic.Label, tr(this, "", "Total Tags"))
                 #    ),
                 #  e(ui.Statistic,
                 #    e(ui.Statistic.Value, 0),
                 #    e(ui.Statistic.Label, tr(this, "", "Galleries without tags"))
                 #    ),
                 #  size="mini",
                 #  ),
                 e(ui.Divider, hidden=True, section=True),
                 e(ui.Search, placeholder=tr(this, "", "Search tags"), fluid=True,
                   js_input={'fluid': True}),
                 clearing=True
                 ),
               e(ui.Segment, e(ui.Label.Group, *tag_lbl, size="large"), secondary=True, basic=True,
                 loading=this.state.data_loading)
               ))


TagsPage = createReactClass({
    'displayName': 'TagsPage',

    'getInitialState': lambda: {
        'data': {},
        'data_loading': False,
    },

    'get_tags': get_db_tags,

    #'componentDidMount': lambda: this.get_tags(),

    'render': tagspage_render
})

Page = createReactClass({
    'displayName': 'DirectoryPage',

    'componentWillMount': lambda: this.props.menu([
        e(ui.Menu.Item, js_name=tr(this, "", "Artists"), as_=NavLink,
          to="/directory/artists", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "", "Tags"), as_=NavLink,
          to="/directory/tags", activeClassName="active"),
    ], pointing=True),

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Segment,
                        e(Switch,
                            e(Route, path="/directory/tags", component=TagsPage),
                            e(Route, path="/directory/artists", component=ArtistsPage),
                            e(Redirect, js_from="/directory", exact=True, to={'pathname': "/directory/tags"}),
                          ),
                        basic=True,
                        )
})
