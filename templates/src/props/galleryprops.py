from src.react_utils import (h,
                             e,
                             createReactClass)
from src import utils
from src.state import state
from src.ui import ui, RemovableItem
from src.i18n import tr
from src.single import artistitem, parodyitem, circleitem
from src.client import ItemType, client
from src.props import simpleprops
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

def update_title(value, id):
    t = utils.lodash_find(this.state.data, lambda v, i, c: v['id']==id)
    if t:
        t.js_name = value
        this.update_data(this.state.data)

def update_title_language(value, id):
    t = utils.lodash_find(this.state.data, lambda v, i, c: v['id']==id)
    if t:
        t.language = value
        this.update_data(this.state.data)

def remove_title(e, d):
    tid = e.target.dataset.id
    data = this.props.data or this.state.data
    if tid and data:
        ndata = utils.remove_from_list(data, {'id': tid})
        this.update_data(ndata)
            

def titles_render():
    data = this.props.data or this.state.data

    pref_el = []
    pref_title = ""
    if this.props.preferred and not this.props.edit_mode:
        pref_title = this.props.preferred.js_name
        pref_el.append(e(ui.Table.Row,
                        e(ui.Table.Cell, e(ui.Header, pref_title, size="medium"),
                          colSpan="2", textAlign="center"),
                        )
                       )

    els = []

    if data:
        for t in data:
            if t.js_name == pref_title and not this.props.edit_mode:
                continue
            els.append(e(ui.Table.Row,
                        e(ui.Table.Cell, e(simpleprops.Language, data_id=t.id, update_data=this.update_language, edit_mode=this.props.edit_mode, data=t.language, size="tiny", className="sub-text" if not this.props.edit_mode else ""), collapsing=True),
                        e(ui.Table.Cell, e(ui.Header, h("span", e(ui.Icon, js_name="remove", onClick=this.on_remove, link=True, **{'data-id': t.id}), className="right") if this.props.edit_mode else None,
                                           e(simpleprops.EditText,
                                             defaultValue=t.js_name,
                                             edit_mode=this.props.edit_mode,
                                             update_data=this.update_title,
                                             data_id=t.id,
                                             fluid=True),
                                           size="tiny", className="sub-text" if not this.props.edit_mode else "")),
                        key=t.id,
                        )
                        )

    return e(ui.Table,
             *pref_el,
             this.props.children if this.props.children else els,
             size=this.props.size,
             basic="very",
             className=this.props.className,
             as_=this.props.as_)

Titles = createReactClass({
    'displayName': 'Titles',

    'getInitialState': lambda: {
                                'data': this.props.data or [],
                                },
    'update_title': update_title,
    'update_language': update_title_language,
    'on_click': lambda: this.setState({'edit_mode': True}),
    'update_data': utils.update_data,
    'on_remove': remove_title,
    'render': titles_render
})

def update_artist(e, d):
    if this.props.on_update:
        this.props.on_update({'id': d.value}, "add")
    this.setState({'edit_mode': False})

def remove_artist(e, d):
    tid = e.target.dataset.id
    data = this.props.data or this.state.data
    if tid and data:
        ndata = utils.remove_from_list(data, {'id': tid})
        this.setState({'data': ndata})
            

def artists_render():
    data = this.props.data or this.state.data

    els = []

    if data:
        for a in data:
            els.append(e(artistitem.ArtistLabel,
                         data=a,
                         key=a.id,
                         edit_mode=this.props.edit_mode,
                         onRemove=this.on_remove
                        )
                        )

    return els

Artists = createReactClass({
    'displayName': 'Artists',

    'getInitialState': lambda: {
                                'data': this.props.data or [],
                                'edit_mode': False,
                                },
    'update': update_artist,
    'on_click': lambda: this.setState({'edit_mode': True}),
    'on_remove': remove_artist,
    'render': artists_render
})

def get_status(data=None, error=None):
    if data is not None and not error:
        this.setState({'all_data': data})
    elif error:
        pass
    else:
        client.call_func("get_items", this.get_items,
                         item_type=ItemType.Status,
                         _memoize=60*10)

def status_update(e, d):
    if isinstance(d.value, int):
        data = {'id': d.value}
    else:
        data = {'name': d.value}
    create_val = {}
    if this.props.grouping_id:
        create_val = {'id': this.props.grouping_id}
    if this.props.update_data:
        if this.props.data_key:
            this.props.update_data(data, this.props.data_key, new_data_key="grouping", create=create_val)
        elif this.props.data_id:
            this.props.update_data(data, this.props.data_id, new_data_key="grouping", create=create_val)

    this.setState({'edit_mode': False})

def status_render():
    data = this.props.data or this.state.data
    if data.id and not data.js_name:
        data = utils.lodash_find(this.state.all_data, lambda v, i, c: v['id']==data.id) or data
    el = None
    stat_name = data.js_name or tr(this, "ui.t-unknown", "Unknown")
    if this.state.edit_mode:
        options = []
        for i in this.state.all_data:
            options.append({'key': i.id, 'value': i.id, 'text': i.js_name})
        el = e(ui.Select,
                options=options,
                placeholder=tr(this, "ui.t-status", "Status"),
                 defaultValue=data.id,
                 size=this.props.size,
                 basic=this.props.basic,
                 compact=this.props.compact,
                 as_=this.props.as_,
                 onChange=this.on_update,
                 onBlur=this.on_blur,)
    elif data:
        el = e(ui.Label,
                 stat_name,
                 color={"completed": "green",
                        "ongoing": "orange",
                        "unreleased": "red",
                        "unknown": "grey"}.get(stat_name.lower(), "blue"),
                 size=this.props.size,
                 basic=this.props.basic,
                 className=this.props.className,
                 onClick=this.on_click if this.props.edit_mode else js_undefined,
                 onRemove=this.on_remove if this.props.edit_mode else js_undefined,
                 as_=this.props.as_ if utils.defined(this.props.as_) else "a" if this.props.edit_mode else js_undefined)

    return el

Status = createReactClass({
    'displayName': 'Status',

    'getInitialState': lambda: {
                                'data': this.props.data or {},
                                'all_data': [],
                                'edit_mode': False,
                                },

    "get_items": get_status,
    'componentDidMount': lambda: this.get_items(),
    'on_update': status_update,
    'on_click': lambda: this.setState({'edit_mode': True}),
    #'on_blur': lambda: this.setState({'edit_mode': False}),
    'on_remove': lambda: print("remove"),
    'render': status_render
})

def description_render():
    data = this.props.data or this.state.data
    el = None
    if this.props.edit_mode:
        el = h("div",
               e(simpleprops.EditText,
                 update_data=this.props.update_data,
                 data_key=this.props.data_key,
                 defaultValue=data,
               edit_mode=this.props.edit_mode,
               fluid=utils.defined_or(this.props.fluid, True),
               as_=ui.TextArea),
               className="ui form")
    else:
        el = e(ui.Header, data, size="tiny", className="sub-text")

    return el

Description = createReactClass({
    'displayName': 'Description',

    'getInitialState': lambda: {
                                'data': this.props.data,
                                },
    'on_change': lambda e, d: this.setState({'data': d.value}),
    'render': description_render
})