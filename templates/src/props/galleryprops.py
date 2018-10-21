from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui
from src import utils
from src.i18n import tr
from src.single import artistitem, parodyitem
from src.selectors import artistselector, parodyselector
from src.client import ItemType, client
from src.props import simpleprops
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
screen = Object = Date = None
__pragma__('noskip')


def update_title(value, n):
    data = this.props.data or this.state.data
    t = utils.find_in_list(data, n, index=True)
    if t:
        t.js_name = value
        this.update_data(data)


def update_title_language(value, n):
    data = this.props.data or this.state.data
    t = utils.find_in_list(data, n, index=True)
    if t:
        t.language = value
        this.update_data(data)


def remove_title(e, d):
    tid = e.target.dataset.id
    data = this.props.data or this.state.data
    if tid and data:
        ndata = utils.remove_from_list(data, tid, index=True)
        this.update_data(ndata)


def titles_update(p_p, p_s):
    if any((
        p_p.edit_mode != this.props.edit_mode,
    )):
        this.setState({'data': []})


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
        for n, t in enumerate(data):
            if t.js_name == pref_title and not this.props.edit_mode:
                continue
            els.append(e(ui.Table.Row,
                         e(ui.Table.Cell,
                           e(simpleprops.Language,
                             data_id=n,
                             update_data=this.update_language,
                             edit_mode=this.props.edit_mode,
                             data=t.language,
                             size="tiny",
                             className="sub-text" if not this.props.edit_mode else ""),
                             collapsing=True),
                         e(ui.Table.Cell, e(ui.Header, h("span", e(ui.Icon, js_name="remove", onClick=this.on_remove, link=True, **{'data-id': n}), className="right") if this.props.edit_mode else None,
                                            e(simpleprops.EditText,
                                              defaultValue=t.js_name,
                                              defaultOpen=not bool(t.js_name),
                                              edit_mode=this.props.edit_mode,
                                              update_data=this.update_title,
                                              data_id=n,
                                              fluid=True),
                                            size="tiny", className="sub-text" if not this.props.edit_mode else "")),
                         key=n + t.js_name,
                         )
                       )

    if this.props.edit_mode:
        els.append(e(ui.Table.Row,
                     e(ui.Table.Cell,
                       e(ui.Header, h("span", e(ui.Icon, color="green", js_name="plus", onClick=this.on_create_item, link=True), className="right"),
                         size="tiny"),
                       #e(ui.Icon, js_name="plus", color="green"),
                       colSpan="2"),
                     key="add"))

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
    'on_create_item': lambda: all((this.props.data.append({}), this.setState({'data': utils.JSONCopy(this.props.data)}))),
    # 'cancel_create_item': lambda: this.setState({'create_item': False}),
    'update_data': utils.update_data,
    'on_remove': remove_title,
    'componentDidUpdate': titles_update,
    'render': titles_render
})

__pragma__("kwargs")


def artist_update_data(*args, **kwargs):
    kwargs['propagate'] = False
    kwargs['only_return'] = True
    kwargs['merge_key'] = False
    data = this.update_data(*args, **kwargs)
    this.update_data(data)


__pragma__("nokwargs")


def on_new_artist(e, data):
    for a in data:
        this.update_data(a, op="append")


def remove_artist(e, d):
    e.preventDefault()
    tid = e.target.dataset.id
    tname = e.target.dataset.js_name
    data = this.props.data or this.state.data
    if tid and data:
        tid = int(tid)
        ndata = utils.remove_from_list(data, tid, key="id")
        this.update_data(ndata)
    if tname and data:
        ndata = utils.remove_from_list(data, tname, key="preferred_name.name")
        this.update_data(ndata)


def artists_update(p_p, p_s):
    if any((
        p_s.new_data != this.state.new_data,
    )):
        this.update_data(this.state.data)


def artists_render():
    data = this.props.data or this.state.data

    els = []
    if data:
        idx = {}
        for n, x in enumerate(data):
            idx[x] = n
        for a in sorted(data, key=lambda x: utils.get_object_value('preferred_name.name')):
            els.append(e(artistitem.ArtistLabel,
                         data=a,
                         key=a.id or utils.get_object_value(
                             'preferred_name.name', a) or utils.get_object_value(
                             'names[0].name', a),
                         edit_mode=this.props.edit_mode,
                         update_data=this.artist_update_data,
                         data_key='[' + idx[a] + ']',
                         onRemove=this.on_remove
                         )
                       )

    if this.props.edit_mode:
        els.append(e(ui.Modal,
                     e(ui.Modal.Content,
                       onSubmit=this.on_new_artist,
                       scrolling=True,
                       onClose=this.on_modal_toggle,
                       defaultSelected=data,
                       as_=artistselector.ArtistSelector),
                     trigger=e(
                         ui.Icon,
                         onClick=this.on_modal_toggle,
                         size="small",
                         link=True,
                         js_name="plus",
                         color="blue"),
                     dimmer="inverted",
                     size="small",
                     closeOnDocumentClick=True,
                     centered=False,
                     closeIcon=True,
                     open=this.state.modal_open,
                     onClose=this.on_modal_toggle,
                     ))

    els = e(ui.Label.Group, els)

    return els


Artists = createReactClass({
    'displayName': 'Artists',

    'getInitialState': lambda: {
        'data': this.props.data or [],
        'modal_open': False,
    },
    'on_new_artist': on_new_artist,
    'on_click': lambda: this.setState({'edit_mode': True}),
    'on_modal_toggle': lambda: this.setState({'modal_open': not this.state.modal_open}),
    'on_remove': remove_artist,
    'artist_update_data': artist_update_data,
    'update_data': utils.update_data,
    'componentDidUpdate': artists_update,
    'render': artists_render
})


def get_status(data=None, error=None):
    if data is not None and not error:
        this.setState({'all_data': data, 'loading': False})
    elif error:
        pass
    else:
        this.setState({'loading': True})
        client.call_func("get_items", this.get_items,
                         item_type=ItemType.Status,
                         _memoize=60 * 10)


def status_update(e, d):
    if isinstance(d.value, int):
        data = {'id': d.value}
    else:
        data = {'name': d.value}
        this.state.all_data.append(data)
        all_data = utils.unique_list(this.state.all_data, key='name')
        this.setState({'all_data': all_data})

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
        data = utils.lodash_find(this.state.all_data, lambda v, i, c: v['id'] == data.id) or data
    el = None
    stat_name = data.js_name or tr(this, "ui.t-unknown", "Unknown")
    if this.state.edit_mode:
        options = []
        for i in this.state.all_data:
            options.append({'key': i.id or i.js_name, 'value': i.id or i.js_name, 'text': i.js_name})
        el = e(ui.Select,
               options=options,
               placeholder=tr(this, "ui.t-status", "Status"),
               defaultValue=data.id,
               size=this.props.size,
               basic=this.props.basic,
               compact=this.props.compact,
               as_=this.props.as_,
               onChange=this.on_update,
               loading=this.state.loading,
               onBlur=this.on_blur,
               allowAdditions=True,
               search=True,
               additionLabel=tr(this, "ui.t-add", "add") + ' '
               )
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
        'loading': True,
    },

    "get_items": get_status,
    'componentDidMount': lambda: this.get_items(),
    'on_update': status_update,
    'on_click': lambda: this.setState({'edit_mode': True}),
    # 'on_blur': lambda: this.setState({'edit_mode': False}),
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


def get_category_items(data=None, error=None):
    if data is not None and not error:
        this.setState({'all_data': data, 'loading': False})
    elif error:
        pass
    else:
        this.setState({'loading': True})
        client.call_func("get_items", this.get_items,
                         item_type=ItemType.Category,
                         _memoize=60 * 10)


def category_update(e, d):
    if isinstance(d.value, int):
        data = {'id': d.value}
    else:
        data = {'name': d.value}
        this.state.all_data.append(data)
        all_data = utils.unique_list(this.state.all_data, key='name')
        this.setState({'all_data': all_data})

    if this.props.update_data:
        if this.props.data_key:
            this.props.update_data(data, this.props.data_key)
        elif this.props.data_id:
            this.props.update_data(data, this.props.data_id)

    this.setState({'edit_mode': False})


def category_render():
    data = this.props.data or this.state.data
    el = None
    if data.id and not data.js_name:
        data = utils.lodash_find(this.state.all_data, lambda v, i, c: v['id'] == data.id) or data
    cat_name = data.js_name or tr(this, "ui.t-unknown", "Unknown")
    if this.state.edit_mode:
        options = []
        for i in this.state.all_data:
            options.append({'key': i.id or i.js_name, 'value': i.id or i.js_name, 'text': i.js_name})
        el = e(ui.Select,
               options=options,
               placeholder=tr(this, "ui.t-category", "Category"),
               defaultValue=data.id,
               size=this.props.size,
               basic=this.props.basic,
               compact=this.props.compact,
               as_=this.props.as_,
               onChange=this.on_update,
               loading=this.state.loading,
               onBlur=this.on_blur,
               allowAdditions=True,
               search=True,
               additionLabel=tr(this, "ui.t-add", "add") + ' ')

    elif not utils.lodash_lang.isEmpty(data) or this.props.edit_mode:
        el = e(ui.Label,
               cat_name,
               color="black",
               basic=this.props.basic,
               size=this.props.size,
               className=this.props.className,
               onClick=this.on_click if this.props.edit_mode else js_undefined,
               onRemove=this.on_remove if this.props.edit_mode else js_undefined,
               as_=this.props.as_ if utils.defined(this.props.as_) else "a" if this.props.edit_mode else js_undefined)
    return el


Category = createReactClass({
    'displayName': 'Category',

    'getInitialState': lambda: {
        'data': this.props.data or {},
        'all_data': [],
        'edit_mode': False,
        'loading': True,
    },

    "get_items": get_category_items,
    'componentDidMount': lambda: this.get_items(),
    'on_update': category_update,
    'on_click': lambda: this.setState({'edit_mode': True}),
    # 'on_blur': lambda: this.setState({'edit_mode': False}),
    'on_remove': lambda: print("remove"),
    'render': category_render
})


def on_new_parody(e, data):
    for a in data:
        this.update_data(a, op="append")


def remove_parody(e, d):
    e.preventDefault()
    tid = e.target.dataset.id
    tname = e.target.dataset.js_name
    data = this.props.data or this.state.data
    if tid and data:
        tid = int(tid)
        ndata = utils.remove_from_list(data, tid, key="id")
        this.update_data(ndata)
    if tname and data:
        ndata = utils.remove_from_list(data, tname, key="preferred_name.name")
        this.update_data(ndata)


def parodies_render():
    data = this.props.data or this.state.data

    els = []
    if data:
        for a in sorted(data, key=lambda x: utils.get_object_value('preferred_name.name')):
            els.append(e(parodyitem.ParodyLabel,
                         data=a,
                         key=a.id or utils.get_object_value(
                             'preferred_name.name', a) or utils.get_object_value(
                             'names[0].name', a),
                         edit_mode=this.props.edit_mode,
                         update_data=this.props.update_data,
                         data_key=this.props.data_key,
                         onRemove=this.on_remove
                         )
                       )

    if this.props.edit_mode:
        els.append(e(ui.Modal,
                     e(ui.Modal.Content,
                       onSubmit=this.on_new_parody,
                       scrolling=True,
                       onClose=this.on_modal_toggle,
                       defaultSelected=data,
                       as_=parodyselector.ParodySelector),
                     trigger=e(
                         ui.Icon,
                         onClick=this.on_modal_toggle,
                         size="small",
                         link=True,
                         js_name="plus",
                         color="purple"),
                     dimmer="inverted",
                     size="small",
                     closeOnDocumentClick=True,
                     centered=False,
                     closeIcon=True,
                     open=this.state.modal_open,
                     onClose=this.on_modal_toggle,
                     ))

    els = e(ui.Label.Group, els)

    return els


Parodies = createReactClass({
    'displayName': 'Parodies',

    'getInitialState': lambda: {
        'data': this.props.data or [],
        'modal_open': False,
    },
    'on_new_parody': on_new_parody,
    'on_click': lambda: this.setState({'edit_mode': True}),
    'on_modal_toggle': lambda: this.setState({'modal_open': not this.state.modal_open}),
    'on_remove': remove_parody,
    'update_data': utils.update_data,
    'render': parodies_render
})
