from src.react_utils import (e,
                             createReactClass)
from src.state import state
from src.ui import ui
from src.client import ItemType, client
from src import utils
from src.i18n import tr
from src.props import simpleprops
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def get_gallery_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"gallery_count": data['count']})
    elif error:
        state.app.notif("Failed to fetch gallery count ({})".format(this.state.id), level="error")
    else:
        if not this.state.gallery_count and this.state.data:
            client.call_func("get_related_count", this.get_gallery_count,
                             related_type=ItemType.Gallery,
                             item_type=this.state.item_type,
                             item_id=this.state.data.id)


def get_category(data=None, error=None):
    if data is not None and not error:
        this.setState({"category_data": data})
    elif error:
        state.app.notif("Failed to fetch category ({})".format(this.state.id), level="error")
    else:
        if not this.state.category_data and this.state.data and this.state.data.category_id:
            client.call_func("get_item", this.get_category,
                             item_type=ItemType.Category,
                             item_id=this.state.data.category_id)


def collection_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


def collectionprops_render():

    title = ""
    info = ""
    date_pub = None
    date_upd = None
    date_added = None
    #category = this.props.category or this.state.category_data
    if this.props.data:

        if this.props.data.pub_date:
            date_pub = this.props.data.pub_date
        if this.props.data.last_updated:
            date_upd = this.props.data.last_updated
        if this.props.data.timestamp:
            date_added = this.props.data.timestamp
        info = this.props.data.info
        title = this.props.data.js_name

    rows = []

    if this.props.compact:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, title, size="small"), colSpan="2", textAlign="center",
                        verticalAlign="middle")))
    if info:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, info, size="tiny", className="sub-text"), colSpan="2")))

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-published", "Published") +
                                     ':', size="tiny", className="sub-text"), collapsing=True),
                  e(ui.Table.Cell, e(simpleprops.DateLabel, data=date_pub, full=True))))
    if this.props.compact:
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-date-added", "Date added") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, e(simpleprops.DateLabel, data=date_added, format="LLL"))))
        rows.append(e(ui.Table.Row,
                      e(ui.Table.Cell, e(ui.Header, tr(this, "ui.t-last-updated", "Last updated") +
                                         ':', size="tiny", className="sub-text"), collapsing=True),
                      e(ui.Table.Cell, e(simpleprops.DateLabel, data=date_upd, format="LLL"))))

    return e(ui.Table,
             e(ui.Table.Body,
               *rows
               ),
             basic="very",
             size=this.props.size,
             compact="very" if utils.defined(this.props.compact) else False,
             )


CollectionProps = createReactClass({
    'displayName': 'CollectionProps',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'category_data': this.props.category,
                                'gallery_count': this.props.gallery_count,
                                'item_type': ItemType.Collection,
                                },
    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidMount': lambda: all((this.get_category(), this.get_gallery_count())),
    'get_category': get_category,
    'get_gallery_count': get_gallery_count,
    'componentDidUpdate': collection_on_update,

    'render': collectionprops_render
})
