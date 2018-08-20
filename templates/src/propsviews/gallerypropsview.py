from src.react_utils import (e,
                             createReactClass)
from src import utils
from src.state import state
from src.ui import ui
from src.client import ItemType, client
from src.single import circleitem
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


def on_rate(e, d):
    e.preventDefault()
    rating = d.rating
    if this.props.edit_mode:
        this.update_data(rating, "rating")


def get_lang(data=None, error=None):
    if data is not None and not error:
        this.setState({"lang_data": data})
    elif error:
        state.app.notif("Failed to fetch language ({})".format(this.state.id), level="error")
    else:
        if this.props.data and not this.props.language and this.props.data.language_id:
            client.call_func("get_item", this.get_lang,
                             item_type=ItemType.Language,
                             item_id=this.props.data.language_id)


def get_category(data=None, error=None):
    if data is not None and not error:
        this.setState({"category_data": data})
    elif error:
        state.app.notif("Failed to fetch category ({})".format(this.state.id), level="error")
    else:
        if this.props.data and not this.props.category and this.props.data.category_id:
            client.call_func("get_item", this.get_category,
                             item_type=ItemType.Category,
                             item_id=this.props.data.category_id)


__pragma__("tconv")


def get_status(data=None, error=None):
    if data is not None and not error:
        if data:
            this.setState({"status_data": data[0]})
    elif error:
        state.app.notif("Failed to fetch status ({})".format(this.state.id), level="error")
    else:
        if this.props.data and not this.props.status and this.props.data.grouping_id:
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
    times_read = 0
    date_pub = None
    date_upd = None
    date_read = None
    date_added = None
    urls = []
    parodies = []
    circles = []
    status = this.props.status or this.state.status_data
    language = this.props.language or this.state.lang_data
    category = this.props.category or this.state.category_data
    tags = this.props.tags or this.state.tags_data
    titles = []
    title_data = None
    grouping_id = None
    if this.props.data:
        if this.props.data.id:
            item_id = this.props.data.id
        if this.props.data.grouping_id:
            grouping_id = this.props.data.grouping_id

        if this.props.data.parodies:
            parodies = this.props.data.parodies
        if this.props.data.titles:
            titles = this.props.data.titles  # noqa: F841

        if this.props.data.pub_date:
            date_pub = this.props.data.pub_date
        if this.props.data.last_updated:
            date_upd = this.props.data.last_updated
        if this.props.data.last_read:
            date_read = this.props.data.last_read
        if this.props.data.timestamp:
            date_added = this.props.data.timestamp
        if this.props.data.times_read:
            times_read = this.props.data.times_read
        if this.props.data.info:
            info = this.props.data.info
        if this.props.data.preferred_title:
            title = this.props.data.preferred_title.js_name # noqa: F841
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

        if this.props.data.language:
            language = this.props.data.language

        if this.props.data.category:
            category = this.props.data.category

        if this.props.data.grouping and this.props.data.grouping.status:
            status = this.props.data.grouping.status

        if this.props.data.urls:
            urls = this.props.data.urls

        if this.props.data.taggable and not utils.lodash_lang.isEmpty(this.props.data.taggable.tags):
            tags = this.props.data.taggable.tags

        if not utils.lodash_lang.isEmpty(this.props.data.tags):
            tags = this.props.data.tags

        if not utils.defined(rating) and utils.defined(this.props.data.rating):
            rating = this.props.data.rating

    paths = []
    if this.props.sources:
        paths = this.props.sources

    rows = []
    if this.props.compact or this.props.new_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-title", "Title") +
                                         ':', size="tiny", className="sub-text"), collapsing=True) if this.props.new_mode else None,
                      e(ui.Table.Cell, e(galleryprops.Titles,
                                         data=titles,
                                         preferred=title_data,
                                         update_data=this.update_data,
                                         data_key="titles",
                                         edit_mode=this.props.edit_mode,
                                         size="small"), colSpan="1" if this.props.new_mode else "2",
                        verticalAlign="middle")))
    if info or this.props.edit_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-description", "Description") +
                                         ':', size="tiny", className="sub-text"), collapsing=True) if this.props.new_mode else None,
                      e(ui.Table.Cell, e(galleryprops.Description,
                                         data=info,
                                         update_data=this.update_data,
                                         data_key="info",
                                         edit_mode=this.props.edit_mode), colSpan="1" if this.props.new_mode else "2")))

    if this.props.compact or this.props.new_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell,
                        e(simpleprops.DateLabel,
                          update_data=this.update_data,
                          data_key="timestamp",
                          edit_mode=this.props.edit_mode,
                          text=tr(this, "ui.t-date-added", "Date added"),
                          data=date_added, format="LLL"),
                        e(simpleprops.DateLabel,
                          update_data=this.update_data,
                          data_key="last_read",
                          edit_mode=this.props.edit_mode,
                          text=tr(this, "ui.t-last-read", "Last read"),
                          data=date_read, format="LLL"),
                        e(simpleprops.DateLabel,
                          update_data=this.update_data,
                          data_key="last_updated",
                          edit_mode=this.props.edit_mode,
                          text=tr(this, "ui.t-last-updated", "Last updated"),
                          data=date_upd, format="LLL",
                          disabled=True if this.props.edit_mode else False) if not this.props.edit_mode else None,
                        colSpan="2",
                        textAlign="center",
                        )))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-artist", "Artist") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(galleryprops.Artists,
                                     data=artists,
                                     update_data=this.update_data,
                                     data_key="artists",
                                     edit_mode=this.props.edit_mode))))
    if circles and not this.props.edit_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-circle", "Circle") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, e(ui.Label.Group, [e(circleitem.CircleLabel, data=x, key=x) for x in circles]))))
    if parodies or this.props.edit_mode:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-parody", "Parody") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, e(galleryprops.Parodies,
                                         data=parodies,
                                         update_data=this.update_data,
                                         data_key="parodies",
                                         edit_mode=this.props.edit_mode))))

    if (this.props.compact and category) or (this.props.edit_mode and not this.props.main):
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-category", "Category") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, e(galleryprops.Category,
                                         data=category,
                                         update_data=this.update_data,
                                         data_key="category",
                                         edit_mode=this.props.edit_mode))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-language", "Language") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.Language,
                                     data=language,
                                     update_data=this.update_data,
                                     data_key="language",
                                     edit_mode=this.props.edit_mode))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-rating", "Rating") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Rating, onRate=this.props.on_rate or this.on_rate, icon="star", rating=rating, maxRating=10, size="huge", clearable=True))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-status", "Status") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(galleryprops.Status,
                                     update_data=this.update_data,
                                     grouping_id=grouping_id,
                                     data_key="grouping.status",
                                     data=status,
                                     edit_mode=this.props.edit_mode))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-published", "Published") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.DateLabel,
                                     update_data=this.update_data,
                                     data_key="pub_date",
                                     edit_mode=this.props.edit_mode,
                                     data=date_pub, full=True))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-times-read", "Times read") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.EditNumber,
                                     data_key="times_read",
                                     update_data=this.update_data,
                                     data=times_read,
                                     edit_mode=this.props.edit_mode))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-tags", "Tags") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(tagview.TagView,
                                     data_key='taggable.tags',
                                     update_data=this.update_data,
                                     single=this.props.single_tags,
                                     edit_mode=this.props.edit_mode,
                                     submitted_data=this.props.submitted_data,
                                     item_id=item_id,
                                     item_type=this.state.item_type,
                                     data=tags,
                                     on_tags=this.props.on_tags))))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-external-links", "External") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.URLs,
                                     data_key="urls",
                                     update_data=this.update_data,
                                     edit_mode=this.props.edit_mode,
                                     data=urls, relaxed=True, size="small"))))

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


GalleryProps = createReactClass({
    'displayName': 'GalleryProps',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                'lang_data': this.props.language,
                                'tags_data': this.props.tags,
                                'category_data': this.props.category,
                                'status_data': this.props.status,
                                'sources': this.props.sources,
                                },
    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidMount': lambda: all((this.get_lang() if not this.props.new_mode else None,
                                      this.get_status() if not this.props.new_mode else None,
                                      this.get_category() if not this.props.new_mode else None)),
    'on_rate': on_rate,
    'get_lang': get_lang,
    'get_status': get_status,
    'get_category': get_category,
    'update_data': utils.update_data,
    'componentDidUpdate': gallery_on_update,

    'render': galleryprops_render
})
