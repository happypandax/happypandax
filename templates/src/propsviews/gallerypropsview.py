from src.react_utils import (h,
                             e,
                             createReactClass)
from src import utils
from src.state import state
from src.ui import ui
from src.client import ItemType, client
from src.single import artistitem, parodyitem, circleitem
from src.views import tagview
from src.props import galleryprops, simpleprops
from src.i18n import tr
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def get_lang(data=None, error=None):
    if data is not None and not error:
        this.setState({"lang_data": data})
    elif error:
        state.app.notif("Failed to fetch language ({})".format(this.state.id), level="error")
    else:
        if this.props.data and not this.props.language:
            client.call_func("get_item", this.get_lang,
                             item_type=ItemType.Language,
                             item_id=this.props.data.language_id)


__pragma__("tconv")


def get_status(data=None, error=None):
    if data is not None and not error:
        if data:
            this.setState({"status_data": data[0]})
    elif error:
        state.app.notif("Failed to fetch status ({})".format(this.state.id), level="error")
    else:
        if this.props.data and not this.props.status:
            client.call_func("get_related_items", this.get_status,
                             item_type=ItemType.Grouping,
                             related_type=ItemType.Status,
                             item_id=this.props.data.grouping_id)


__pragma__("notconv")


def gallery_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


__pragma__('tconv')


def galleryprops_render():

    title = ""
    rating = this.props.rating
    artists = []
    item_id = this.props.id
    info = ""
    read_count = 0
    date_pub = None
    date_upd = None
    date_read = None
    date_added = None
    urls = []
    parodies = []
    circles = []
    status = this.props.status or this.state.status_data
    language = this.props.language or this.state.lang_data
    tags = this.props.tags
    titles = []
    title_data = None
    if this.props.data:
        if this.props.data.id:
            item_id = this.props.data.id
        if this.props.data.parodies:
            parodies = this.props.data.parodies
        if this.props.data.titles:
            titles = this.props.data.titles # noqa: F841

        if this.props.data.pub_date:
            date_pub = this.props.data.pub_date
        if this.props.data.last_updated:
            date_upd = this.props.data.last_updated
        if this.props.data.last_read:
            date_read = this.props.data.last_read
        if this.props.data.timestamp:
            date_added = this.props.data.timestamp
        if this.props.data.read_count:
            read_count = this.props.data.read_count
        if this.props.data.info:
            info = this.props.data.info
        if this.props.data.preferred_title:
            title = this.props.data.preferred_title.js_name
            title_data = this.props.data.preferred_title

        if this.props.data.artists:
            artists = this.props.data.artists
            circle_ids = []
            for a in artists:
                if a.circles:
                    for c in a.circles:
                        if c.id in circle_ids:
                            continue
                        circles.append(c)
                        circle_ids.append(c.id)

        if this.props.data.urls:
            urls = this.props.data.urls

        if not utils.defined(rating) and this.props.data.rating:
            rating = this.props.data.rating

    rows = []
    if this.props.compact:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(galleryprops.Titles,
                                         data=titles,
                                         preferred=title_data,
                                         update_data=this.props.update_data,
                                         data_key="titles",
                                         edit_mode=this.props.edit_mode,
                                         size="small"), colSpan="2",
                        verticalAlign="middle")))
    if info or this.props.edit_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(galleryprops.Description,
                                         data=info,
                                         update_data=this.props.update_data,
                                         data_key="info",
                                         edit_mode=this.props.edit_mode), colSpan="2")))

    if this.props.compact:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell,
                        e(simpleprops.DateLabel,
                          update_data=this.props.update_data,
                          data_key="timestamp",
                          edit_mode=this.props.edit_mode,
                          text=tr(this, "ui.t-date-added","Date added"),
                          data=date_added, format="LLL"),
                        e(simpleprops.DateLabel,
                          update_data=this.props.update_data,
                          data_key="last_read",
                          edit_mode=this.props.edit_mode,
                          text=tr(this, "ui.t-last-read", "Last read"),
                          data=date_read, format="LLL"),
                        e(simpleprops.DateLabel,
                          update_data=this.props.update_data,
                          data_key="last_updated",
                          edit_mode=this.props.edit_mode,
                          text=tr(this, "ui.t-last-updated", "Last updated"),
                          data=date_upd, format="LLL",
                          disabled=True if this.props.edit_mode else False),
                        colSpan="2",
                        textAlign="center",
                        )))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-artist", "Artist") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(galleryprops.Artists,
                                     data=artists,
                                     update_data=this.props.update_data,
                                     data_key="artists",
                                     edit_mode=this.props.edit_mode))))
    if circles and not this.props.edit_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-circle", "Circle") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, *(e(circleitem.CircleLabel, data=x) for x in circles))))
    if parodies or this.props.edit_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-parody", "Parody") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, *(e(parodyitem.ParodyLabel,data=x) for x in parodies))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-language", "Language") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.Language,
                                     data=language,
                                     update_data=this.props.update_data,
                                     data_key="language",
                                     edit_mode=this.props.edit_mode))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-rating", "Rating") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Rating, icon="star", rating=rating, maxRating=10, size="huge", clearable=True))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-status", "Status") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(galleryprops.Status,
                                     update_data=this.props.update_data,
                                     data_key="language",
                                     data=status,
                                     edit_mode=this.props.edit_mode))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-published", "Published") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.DateLabel,
                                     update_data=this.props.update_data,
                                     data_key="pub_date",
                                     edit_mode=this.props.edit_mode,
                                     data=date_pub, full=True))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-times-read", "Times read") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.EditNumber,
                                     data_key="read_count",
                                     update_data=this.props.update_data,
                                     data=read_count,
                                     edit_mode=this.props.edit_mode))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-tags", "Tags") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(tagview.TagView,
                                     data_key="tags",
                                     update_data=this.props.update_data,
                                     edit_mode=this.props.edit_mode,
                                     item_id=item_id,
                                     item_type=this.state.item_type, data=tags, on_tags=this.props.on_tags))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-external-links", "External") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.URLs,
                                     data_key="urls",
                                     update_data=this.props.update_data,
                                     edit_mode=this.props.edit_mode,
                                     data=urls, relaxed=True, size="small"))))

    return e(ui.Table,
             e(ui.Table.Body,
               *rows
               ),
             basic="very",
             size=this.props.size,
             compact="very" if utils.defined(this.props.compact) else False,
             )


__pragma__('notconv')


GalleryProps = createReactClass({
    'displayName': 'GalleryProps',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                'lang_data': this.props.language,
                                'status_data': this.props.status,
                                },
    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidMount': lambda: all((this.get_lang(), this.get_status())),
    'get_lang': get_lang,
    'get_status': get_status,
    'componentDidUpdate': gallery_on_update,

    'render': galleryprops_render
})


def update_data(g):
    new_g = utils.JSONCopy(g)
    this.setState({'data': new_g})
    if this.props.on_data_update:
        this.props.on_data_update(new_g)


def on_rate(e, d):
    this.state.data.rating = d.rating
    this.update_data(this.state.data)


def newgalleryprops_render():

    rating = this.props.rating
    artists = []
    item_id = this.props.id
    info = ""
    read_count = 0
    date_pub = None
    date_upd = None
    date_read = None
    date_added = None
    urls = []
    parodies = []
    circles = []
    titles = []
    status = this.props.status or this.state.status_data
    language = this.props.language or this.state.lang_data
    tags = this.props.tags
    if this.props.data:
        if this.props.data.id:
            item_id = this.props.data.id
        if this.props.data.parodies:
            parodies = this.props.data.parodies
        if this.props.data.titles:
            titles = this.props.data.titles

        if this.props.data.pub_date:
            date_pub = this.props.data.pub_date
        if this.props.data.last_updated:
            date_upd = this.props.data.last_updated # noqa: F841
        if this.props.data.last_read:
            date_read = this.props.data.last_read # noqa: F841
        if this.props.data.timestamp:
            date_added = this.props.data.timestamp # noqa: F841
        if this.props.data.read_count:
            read_count = this.props.data.times_read # noqa: F841
        if this.props.data.info:
            info = this.props.data.info

        if this.props.data.artists:
            artists = this.props.data.artists
            circle_ids = []
            for a in artists:
                if a.circles:
                    for c in a.circles:
                        if c.id in circle_ids:
                            continue
                        circles.append(c)
                        circle_ids.append(c.id)

        if this.props.data.urls:
            for u in this.props.data.urls:
                urls.append(u.js_name)

        if not utils.defined(rating) and this.props.data.rating:
            rating = this.props.data.rating

        if not language and this.props.data.language:
            language = this.props.data.language

        if not status and this.props.data.status:
            status = this.props.data.status

        if not tags and this.props.data.taggable and this.props.data.taggable.tags:
            tags = this.props.data.taggable.tags

    paths = []
    if this.props.sources:
        paths = this.props.sources

    status = status.js_name if status else tr(this, "ui.t-unknown", "Unknown")
    language = language.js_name if language else tr(this, "ui.t-unknown", "Unknown")

    rows = []

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-title", "Title") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(galleryprops.Titles,
                                     data=titles,
                                     update_data=this.props.update_data,
                                     data_key="titles",
                                     size="small"))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-description", "Description") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Header, info, size="tiny", className="sub-text"))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-artist", "Artist") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, *(e(artistitem.ArtistLabel, data=x) for x in artists))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-circle", "Circle") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, *(e(circleitem.CircleLabel, data=x) for x in circles))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-parody", "Parody") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, *(e(parodyitem.ParodyLabel, data=x) for x in parodies))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-language", "Language") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, language)))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-rating", "Rating") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Rating, onRate=this.on_rate, icon="star", rating=rating, maxRating=10, size="huge", clearable=True))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-status", "Status") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, tr(this, "general.db-status-{}".format(status.lower()), status), color={"completed": "green",
                                                                                                                       "ongoing": "orange",
                                                                                                                       "unreleased": "red",
                                                                                                                       "unknown": "grey"}.get(status.lower(), "blue")))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-published", "Published") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.DateLabel, data=date_pub, full=True))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-tags", "Tags") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(tagview.TagView, item_id=item_id, item_type=this.state.item_type, data=tags, on_tags=this.props.on_tags))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-external-links", "External") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(ui.List, *[e(ui.List.Item, h("span", h("a", x, href=x, target="_blank"), e(ui.List.Icon, js_name="external share"))) for x in urls], size="small", relaxed=True))))

    if paths:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-path", "Path") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, e(ui.List, *[e(ui.List.Item, e(ui.Header, x, size="tiny", className="sub-text"),) for x in paths], size="tiny", relaxed=True, divided=True))))

    return e(ui.Table,
             e(ui.Table.Body,
               *rows
               ),
             basic="very",
             size=this.props.size,
             compact="very" if utils.defined(this.props.compact) else False,
             )


__pragma__('notconv')


NewGalleryProps = createReactClass({
    'displayName': 'NewGalleryProps',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data or {},
                                'item_type': ItemType.Gallery,
                                'lang_data': this.props.language,
                                'status_data': this.props.status,
                                'sources': this.props.sources,
                                },
    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    # 'componentDidMount': lambda: all((this.get_lang(), this.get_status())),
    'get_lang': get_lang,
    'get_status': get_status,
    'update_data': update_data,
    'on_rate': on_rate,

    'render': newgalleryprops_render
})
