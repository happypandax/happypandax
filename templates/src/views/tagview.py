from src.react_utils import (e, createReactClass)
from src.ui import ui
from src.client import client
from src.state import state
from src import utils
from src.single import tagitem
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def get_tags(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data})
        if this.props.on_tags:
            this.props.on_tags(data)
    elif error:
        state.app.notif("Failed to fetch tags ({})".format(this.props.item_id), level="error")
    else:
        if this.props.item_id and this.props.item_type:
            args = {}
            args['item_id'] = this.props.item_id
            args['item_type'] = this.props.item_type
            if utils.defined(this.props.raw):
                args['raw'] = this.props.raw

            client.call_func("get_tags", this.get_tags, **args)


def tag_on_update(p_props, p_state):
    if any((
        p_props.item_id != this.props.item_id,
        p_props.item_type != this.props.item_type,
        p_props.raw != this.props.raw,
    )):
        this.get_tags()

    if p_props.data != this.props.data:
        this.setState({'data': this.props.data})


def tag_render():

    tag_rows = []
    data = this.state.data

    if isinstance(data, list):
        d = {}
        for nstag in data:
            if not d[nstag.namespace.js_name]:
                d[nstag.namespace.js_name] = []
            d[nstag.namespace.js_name].append(nstag.tag)
        data = d

    if data.__namespace__:  # somehow transcrypt ignores this in the loop below
        ns_tags = data.__namespace__
        ns_tags = sorted([x.js_name for x in ns_tags])
        tag_rows.append(
            e(ui.Table.Row,
                e(ui.Table.Cell,
                  e(ui.Label.Group,
                    *[e(tagitem.TagLabel, tag=x, show_ns=False) for x in ns_tags],
                    ),
                  colSpan="2",
                  )))
    for ns in sorted(dict(data).keys()):
        ns_tags = this.state.data[ns]
        ns_tags = sorted([x.js_name for x in ns_tags])
        tag_rows.append(
            e(ui.Table.Row,
                e(ui.Table.Cell, ns, className="sub-text", collapsing=True),
                e(ui.Table.Cell,
                  e(ui.Label.Group,
                    *[e(tagitem.TagLabel, namespace=ns, tag=x, show_ns=False) for x in ns_tags],
                    ),
                  )))

    return e(ui.Table,
             e(ui.Transition.Group, *tag_rows, as_=ui.Table.Body, duration=1000),
             basic="very", celled=True, compact="very", size="small")


TagView = createReactClass({
    'displayName': 'TagView',

    'getInitialState': lambda: {'data': this.props.data or {}},

    'get_tags': get_tags,

    'componentDidMount': lambda: this.get_tags() if not utils.defined(this.props.data) else None,
    'componentDidUpdate': tag_on_update,

    'render': tag_render
}, pure=True)
