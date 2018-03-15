from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui
from src.client import ItemType
from src.single import artistitem
from src import utils
from src.views import tagview
from src.i18n import tr
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def gallery_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


def galleryprops_render():
    fav = 0
    title = ""
    rating = 0
    urls = []
    artists = []
    artist_names = []
    item_id = this.state.id
    info = ""
    inbox = False
    date_pub = tr(this, "ui.t-unknown", "Unknown")
    date_read = tr(this, "ui.t-unknown", "Unknown")
    date_added = tr(this, "ui.t-unknown", "Unknown")

    if this.state.data:
        read_count = this.state.data.times_read
        rating = this.state.data.rating
        title = this.state.data.titles[0].js_name
        info = this.state.data.info
        inbox = this.state.data.metatags.inbox

        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id

        for a in this.state.data.artists:
            if len(a.names) > 0:
                artist_names.append(a.names[0].js_name)
        artists = this.state.data.artists

        for u in this.state.data.urls:
            urls.append(u.js_name)

        if this.state.data.pub_date:
            date_pub = utils.moment.unix(this.state.data.pub_date).format("LL")
            date_pub += " (" + utils.moment.unix(this.state.data.pub_date).fromNow() + ")"
        if this.state.data.last_read:
            date_read = utils.moment.unix(this.state.data.last_read).format("LLL")
            date_read += " (" + utils.moment.unix(this.state.data.last_read).fromNow() + ")"
        if this.state.data.timestamp:
            date_added = utils.moment.unix(this.state.data.timestamp).format("LLL")
            date_added += " (" + utils.moment.unix(this.state.data.timestamp).fromNow() + ")"

    rows = []

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, title, as_="h3"), colSpan="2", textAlign="center",
                    verticalAlign="middle")))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, info, as_="h5", className="sub-text"), colSpan="2")))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-multi-artists", "Artist(s)") + ':', as_="h5"), collapsing=True),
                  e(ui.Table.Cell, *(e(artistitem.ArtistLabel, data=x) for x in artists))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-published", "Published") + ':', as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, date_pub))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-date-added", "Date added") + ':', as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, date_added))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-last-read", "Last read") + ':', as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, date_read))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-times-read", "Times read") + ':', as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, read_count, circular=True))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-tags", "Tags") + ':', as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(tagview.TagView, item_id=item_id, item_type=this.state.item_type,
                                     data=this.state.tags, on_tags=this.props.on_tags))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-multi-urls", "URL(s)") + ':', as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.List, *[e(ui.List.Item, h("span", h("a", x, href=x, target="_blank"), e(ui.List.Icon, js_name="external share"))) for x in urls]))))

    return e(ui.Table,
             e(ui.Table.Body,
               *rows
               ),
             basic="very",
             size="small"
             )


GalleryProps = createReactClass({
    'displayName': 'GalleryProps',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                'tags': this.props.tags,
                                },
    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': gallery_on_update,

    'render': galleryprops_render
})
