from src.react_utils import (e, createReactClass)
from src.ui import ui
from src.client import client
from src.state import state
from src import utils
from src.i18n import tr
from src.single import tagitem
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

__pragma__('kwargs')
def update_tags(data=None, error=None, new_data=None):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to update tags ({})".format(this.state.data.id), level="error")
    else:
        new_data = new_data or this.state.new_data
        if new_data:
            client.call_func("update_item_tags", this.update_tags,
                                item_type=this.props.item_type,
                                item_id=this.props.item_id,
                                tags=new_data)
__pragma__('nokwargs')

def tag_on_input(e, d):
    idata = this.state.tags_input
    itags = [x.strip() for x in str(idata).split(',')]

    data = this.props.data or this.state.data or {}
    special_namespace = "__namespace__"
    for t in itags:
        if ':' in t:
            t = t.split(':', 1)
            ns = t[0].capitalize()
            tag = t[1]
        else:
            ns = None
            tag = t

        if not tag:
            continue

        tag = tag.lower()

        tag = {'name': tag}

        data = utils.update_object(ns if ns else special_namespace,
                            utils.JSONCopy(data),
                            tag,
                            op="append",
                            create_value=[],
                            unique=lambda a,b: a['name'] == b['name'])
    this.setState({'tags_input': ''})
    this.update_data(data)

def remove_tag(e, d):
    e.preventDefault()
    tag = e.target.dataset.tag
    ns = e.target.dataset.namespace or '__namespace__'
    data = this.props.data or this.state.data
    if tag and ns and data:
        tags = data[ns]
        data[ns] = utils.remove_from_list(tags, tag, key="name")
        if not len(data[ns]):
            del data[ns]
        this.update_data(data)


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
        p_props.data != this.props.data and utils.is_invalid(this.props.data)
    )):
        if not this.props.data:
            this.get_tags()

    if p_props.edit_mode != this.props.edit_mode:
        can_submit = all((
            not this.props.edit_mode,
            this.props.submitted_data,
            this.props.item_id,
            this.props.item_type,
            ))
        if can_submit:
            this.update_tags()

def tag_render():
    ns_tags
    tag_rows = []
    edit_row = []
    data = this.props.data or this.state.data
    edit_mode = this.props.edit_mode
    remove_tag = this.remove_tag

    if edit_mode:
        edit_row.append(
            e(ui.Table.Row,
              e(ui.Table.Cell,
                e(ui.Form,
                    e(ui.Input,
                      onChange=this.on_input,
                      value=this.state.tags_input,
                      fluid=True,
                      className="secondary",
                      placeholder=tr(this, "ui.t-tag-edit-placeholder", "new tags")),
                    onSubmit=this.on_input_submit,
                  ),
                colSpan="2")))

    if isinstance(data, list):
        d = {}
        for nstag in data:
            if not d[nstag.namespace.js_name]:
                d[nstag.namespace.js_name] = []
            d[nstag.namespace.js_name].append(nstag.tag)
        data = d

    if data and data.__namespace__:  # somehow transcrypt ignores this in the loop below
        ns_tags = data.__namespace__
        ns_tags = sorted(list(ns_tags), key=lambda x: x.js_name)
        tag_rows.append(
            e(ui.Table.Row,
                e(ui.Table.Cell,
                  e(ui.Label.Group,
                    [e(tagitem.TagLabel,
                        tag=x.js_name,
                        key=x.id or Math.random(),
                        id=x.id+'-'+'__namespace__',
                        show_ns=False,
                        onRemove=remove_tag,

                        edit_mode=edit_mode) for x in ns_tags],
                    ),
                  colSpan="2",
                  )))

    if data:
        for ns in sorted(dict(data).keys()):
            ns_tags = data[ns]
            ns_tags = sorted(list(ns_tags), key=lambda x: x.js_name)
            tag_rows.append(
                e(ui.Table.Row,
                    e(ui.Table.Cell, ns, className="sub-text", collapsing=True),
                    e(ui.Table.Cell,
                      e(ui.Label.Group,
                        [e(tagitem.TagLabel,
                            namespace=ns,
                            tag=x.js_name,
                            key=x.id or Math.random(),
                            id=x.id+'-'+ns,
                            onRemove=remove_tag,
                            show_ns=False,
                            edit_mode=edit_mode) for x in ns_tags],
                        ),
                      )))

    return e(ui.Table,
             *edit_row,
             e(ui.Transition.Group, *tag_rows, as_=ui.Table.Body, duration=500),
             basic="very", celled=True, compact="very", size="small")


TagView = createReactClass({
    'displayName': 'TagView',

    'getInitialState': lambda: {'data': {},
                                'tags_input': ''},

    'get_tags': get_tags,
    'update_tags': update_tags,
    'remove_tag': remove_tag,
    'update_data': utils.update_data,

    'on_input_submit': tag_on_input,
    'on_input': lambda e, d: this.setState({'tags_input': d.value}),

    'componentDidMount': lambda: this.get_tags() if not utils.defined(this.props.data) else None,
    'componentDidUpdate': tag_on_update,

    'render': tag_render
}, pure=True)
