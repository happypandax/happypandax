from src import utils
from src.react_utils import (h,
                             e,
                             Link,
                             createReactClass)
from src.ui import ui
from src.i18n import tr
from src.state import state
from src.client import ItemType, client
from src.props import artistprops
from src.single import tagitem
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def artist_favorite(e, d):
    if this.props.edit_mode:
        e.preventDefault()
        this.update_data(bool(d.rating), "metatags.favorite")
    elif this.props.on_favorite:
        this.props.on_favorite(e, d)


def get_tags(data=None, error=None):
    if data is not None and not error:
        this.setState({"tags": data, "loading_tags": False})
        if this.props.on_tags:
            this.props.on_tags(data)
    elif error:
        state.app.notif("Failed to fetch tags ({})".format(this.props.id), level="error")
    else:
        id = this.props.id or this.state.id
        data = this.props.data or this.state.data
        if data:
            id = data.id
        if id:
            this.setState({"loading_tags": True})
            client.call_func("get_common_tags", this.get_tags,
                             item_type=this.state.item_type,
                             item_id=id, limit=10)


def get_gallery_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"gallery_count": data['count']})
    elif error:
        state.app.notif("Failed to fetch gallery count ({})".format(this.props.id), level="error")
    else:
        id = this.props.id or this.state.id
        data = this.props.data or this.state.data
        if data:
            id = data.id
        if id:
            client.call_func("get_related_count", this.get_gallery_count,
                             item_type=this.state.item_type,
                             item_id=id, related_type=ItemType.Gallery)


__pragma__("tconv")


def artistprops_render():
    name = ""
    fav = 0
    nstags = this.props.tags or this.state.tags or {}
    data = this.props.data or this.state.data
    urls = []
    circles = []

    if data:
        if data.preferred_name:
            name = data.preferred_name.js_name
        elif data.names and len(data.names):
            name = data.names[0]
        if data.metatags and data.metatags.favorite:
            fav = 1

        if data.urls:
            for u in data.urls:
                urls.append(u.js_name)

        if data.circles:
            for c in data.circles:
                circles.append(c)

    tag_lbl = []

    if nstags.__namespace__:  # somehow transcrypt ignores this in the loop below
        tags = sorted([x.js_name for x in nstags.__namespace__])
        for t in tags:
            tag_lbl.append(e(tagitem.TagLabel, tag=t))

    for ns in sorted(dict(nstags).keys()):
        tags = [x.js_name for x in nstags[ns]]
        for t in tags:
            tag_lbl.append(e(tagitem.TagLabel, namespace=ns, tag=t, show_ns=True))

    lbl_args = {'content': name}
    if fav:
        lbl_args['icon'] = "star"

    rows = []

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, name, size="medium"), colSpan="2", textAlign="center",
                    verticalAlign="middle")))

    if circles or this.props.edit_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-circle", "Circle") +
                                         ":", size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, e(artistprops.Circles,
                                         data=circles,
                                         update_data=this.update_data,
                                         data_key="circles",
                                         edit_mode=this.props.edit_mode))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-galleries", "Galleries") +
                                     ":", size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, this.state.gallery_count)))

    if urls:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-url", "URL") +
                                         ":", size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, *[e(ui.List.Item, h("span", h("a", x, href=x, target="_blank"), e(ui.List.Icon, js_name="external share"))) for x in urls])))

    slider_el = []

    # slider_el.append(e(ui.Grid.Row, e(ui.Grid.Column,
    #                          e(Slider, *[e(galleryitem.Gallery, data=x) for x in series_data],
    #                            loading=this.state.loading_group,
    #                            secondary=True,
    #                            sildesToShow=4,
    #                            label="Series"),
    #                          )))

    url_search_query = {'search': 'artist:"{}"'.format(name)}

    return e(ui.Grid,
             e(ui.Grid.Row,
                 e(ui.Grid.Column, e(ui.Rating, icon="heart", size="huge", rating=fav, onRate=this.favorite),
                   floated="left", verticalAlign="middle", width=2),
                 e(ui.Grid.Column,
                   e(ui.Button.Group,
                     e(ui.Button, icon="grid layout", title=tr(this, "ui.t-show-galleries", "Show galleries"),
                       as_=Link, to=utils.build_url("/library", query=url_search_query, keep_query=False)),
                     e(ui.Button, icon="heart", title=tr(this, "ui.t-show-fav-galleries", "Show favorite galleries"),
                       as_=Link, to=utils.build_url("/favorite", query=url_search_query, keep_query=False)),
                     basic=True,
                     size="tiny",
                     ),
                   width=14,
                   textAlign="right",
                   verticalAlign="top"
                   ),
               ),
             e(ui.Grid.Row,
                 e(ui.Grid.Column,
                   e(ui.Table,
                     e(ui.Table.Body,
                       *rows
                       ),
                     basic="very",
                     size="small",
                     compact="very",
                     ),)),
             e(ui.Grid.Row, e(ui.Grid.Column,
                              e(ui.Segment,
                                  e(ui.Label, tr(this, "ui.t-most-common-tags", "Most common tags"), attached="top"),
                                  e(ui.Label.Group,
                                    *tag_lbl
                                    ),
                                  basic=True,
                                  loading=this.state.loading_tags,
                                ),
                              width=16), columns=1),
             *slider_el,
             )


ArtistProps = createReactClass({
    'displayName': 'ArtistProps',

    'getInitialState': lambda: {
        'id': this.props.id,
        'data': this.props.data,
        'tags': this.props.tags,
        'item_type': ItemType.Artist,
        'gallery_count': 0,
        'loading_tags': False,
        'new_data': {},
    },

    'update_data': utils.update_data,
    'get_tags': get_tags,
    'favorite': artist_favorite,
    'get_gallery_count': get_gallery_count,


    'componentDidMount': lambda: all((this.get_tags() if not utils.defined(this.props.tags) else None,
                                      this.get_gallery_count())),

    'render': artistprops_render
})
