
__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui
from src.client import client
from src.state import state
from src import utils
from src.single import tagitem


def get_tags(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data})
        if this.props.on_tags:
            this.props.on_tags(data)
    elif error:
        state.app.notif("Failed to fetch tags ({})".format(this.props.id), level="error")
    else:
        if this.props.item_id and this.props.item_type:
            args = {}
            args['item_id'] = this.props.item_id
            args['item_type'] = this.props.item_type
            if utils.defined(this.props.raw):
                args['raw'] = this.props.raw

            client.call_func("get_tags", this.get_tags, **args)


def tag_render():

    tag_rows = []
    if this.state.data.__namespace__:  # somehow transcrypt ignores this in the loop below
        ns_tags = this.state.data.__namespace__
        ns_tags = sorted([x.js_name for x in ns_tags])
        tag_rows.append(
            e(ui.Table.Row,
                e(ui.Table.Cell,
                  e(ui.Label.Group,
                    *[e(tagitem.TagLabel, tag=x, show_ns=False) for x in ns_tags],
                    ),
                  colSpan="2",
                  )))
    for ns in sorted(dict(this.state.data).keys()):
        ns_tags = this.state.data[ns]
        ns_tags = sorted([x.js_name for x in ns_tags])
        tag_rows.append(
            e(ui.Table.Row,
                e(ui.Table.Cell, ns, collapsing=True),
                e(ui.Table.Cell,
                  e(ui.Label.Group,
                    *[e(tagitem.TagLabel, namespace=ns, tag=x, show_ns=False) for x in ns_tags],
                    ),
                  )))

    return e(ui.Table,
             e(ui.Transition.Group, *tag_rows, as_=ui.Table.Body, duration=1000),
             basic="very", celled=True, compact=True)

TagView = createReactClass({
    'displayName': 'TagView',

    'getInitialState': lambda: {'data': this.props.data or {}},

    'get_tags': get_tags,

    'componentDidMount': lambda: this.get_tags() if not utils.defined(this.props.data) else None,

    'render': tag_render
})
