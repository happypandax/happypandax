from src.react_utils import (h,
                             e,
                             createReactClass)
from src import utils
from src.state import state
from src.ui import ui, OnHover
from src.i18n import tr
from src.client import ItemType, client
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

def edittext_update():
    this.update_data(this.state.data)
    this.setState({'edit_mode': False})

def edittext_render():

    el = None

    if this.state.edit_mode and this.props.edit_mode:
        el = e(this.props.as_ or ui.Input,
               defaultValue=this.state.data or this.props.data,
               onChange=this.on_change,
               size=this.props.size or "tiny",
               fluid=this.props.fluid)
        el = e(ui.Form,
               el,
               e(ui.Form.Button, tr(this, "ui.t-submit", "submit"), positive=True, size="mini", floated="right") if this.props.as_==ui.TextArea else None,
               onSubmit=this.on_submit)
    else:
        edit_el = []
        if this.props.edit_mode:
            edit_el.append(h("span", e(ui.Icon, js_name="pencil alternate", link=True, onClick=this.on_click)))
        el = h("div", this.state.data, *edit_el, className="editable" if this.props.edit_mode else "")

    return el

EditText = createReactClass({
    'displayName': 'EditText',

    'getInitialState': lambda: {
                                'edit_mode': utils.defined_or(this.props.defaultOpen, False),
                                'data': this.props.defaultValue,
                                },
    'on_click': lambda: this.setState({'edit_mode': True}),
    'on_change': lambda e, d: this.setState({'data': d.value}),
    'update_data': utils.update_data,
    'on_submit': edittext_update,
    'render': edittext_render
})

def editnumber_update():
    this.update_data(this.state.data)
    this.setState({'edit_mode': False})

def editnumber_render():

    el = None

    if this.state.edit_mode and this.props.edit_mode:
        el = e(ui.Input,
               defaultValue=this.state.data or this.props.data,
               onChange=this.on_change,
               size=this.props.size or "mini",
               js_type="number",
               min=0,
               fluid=this.props.fluid)
        el = e(ui.Form,
               el,
               onSubmit=this.on_submit)
    else:
        if utils.defined_or(this.props.label, True):
            el = e(ui.Label, this.props.data,
                   circular=True,
                   onClick=this.on_click if this.props.edit_mode else js_undefined,
                   color=this.props.color,
                   as_="a" if this.props.edit_mode else js_undefined) 
        else:
            el = e("div", this.props.data,
                   className="editable" if this.props.edit_mode else "",
                   onClick=this.on_click if this.props.edit_mode else js_undefined)

    return el

EditNumber = createReactClass({
    'displayName': 'EditNumber',

    'getInitialState': lambda: {
                                'edit_mode': utils.defined_or(this.props.defaultOpen, False),
                                'data': this.props.defaultValue,
                                },
    'on_click': lambda: this.setState({'edit_mode': True}),
    'on_change': lambda e, d: this.setState({'data': d.value}),
    'update_data': utils.update_data,
    'on_submit': editnumber_update,
    'render': editnumber_render
})

def get_lang_items(data=None, error=None):
    if data is not None and not error:
        this.setState({'all_data': data, 'loading': False})
    elif error:
        pass
    else:
        this.setState({'loading': True})
        client.call_func("get_items", this.get_items,
                         item_type=ItemType.Language,
                         _memoize=60*10)

def language_update(e, d):
    if isinstance(d.value, int):
        data = {'id': d.value}
    else:
        data = {'name': d.value}
    if this.props.update_data:
        if not utils.is_invalid(this.props.data_key):
            this.props.update_data(data, this.props.data_key)
        elif not utils.is_invalid(this.props.data_id):
            this.props.update_data(data, this.props.data_id)

    this.setState({'edit_mode': False})

def language_render():
    data = this.props.data or this.state.data
    el = None
    if data.id and not data.js_name:
        data = utils.lodash_find(this.state.all_data, lambda v, i, c: v['id']==data.id) or data
    lang_name = data.js_name or tr(this, "ui.t-unknown", "Unknown")
    if this.state.edit_mode:
        options = []
        for i in this.state.all_data:
            options.append({'key': i.id, 'value': i.id, 'text': i.js_name})
        el = e(ui.Select,
                options=options,
                placeholder=tr(this, "ui.t-language", "Language"),
                 defaultValue=data.id,
                 size=this.props.size,
                 basic=this.props.basic,
                 compact=this.props.compact,
                 as_=this.props.as_,
                 onChange=this.on_update,
                 loading=this.state.loading,
                 onBlur=this.on_blur,)
    elif data:
        el = e(ui.Label,
                 lang_name,
                 size=this.props.size,
                 basic=this.props.basic,
                 className=this.props.className,
                 onClick=this.on_click if this.props.edit_mode else js_undefined,
                 onRemove=this.on_remove if this.props.edit_mode else js_undefined,
                 as_=this.props.as_ if utils.defined(this.props.as_) else "a" if this.props.edit_mode else js_undefined)

    return el

Language = createReactClass({
    'displayName': 'Language',

    'getInitialState': lambda: {
                                'data': this.props.data or {},
                                'all_data': [],
                                'edit_mode': False,
                                'loading': False,
                                },

    "get_items": get_lang_items,
    'componentDidMount': lambda: this.get_items(),
    'on_update': language_update,
    'on_click': lambda: this.setState({'edit_mode': True}),
    #'on_blur': lambda: this.setState({'edit_mode': False}),
    'on_remove': lambda: print("remove"),
    'render': language_render
})

def datelbl_update(e, d):
    if this.state.data:
        this.update_data(this.state.data)
    this.setState({'edit_mode': False})

def datelbl_render():
    m = None
    data = this.state.data or this.props.data
    if data:
        m = utils.moment.unix(data)
        full = m.format(this.props.format or "LL")
        relative = m.fromNow()
        if this.props.full or this.props.edit_mode:
            date = full + " ({})".format(relative)
        elif this.state.toggled:
            date = full
        else:
            date = relative
    else:
        date = tr(this, "ui.t-unknown", "Unknown")

    el = None
    if this.state.edit_mode and this.props.edit_mode:
        el = e(ui.Input,
               defaultValue=m.format(utils.moment.HTML5_FMT.DATE) if m else js_undefined,
               onChange=this.on_change,
               onBlur=this.on_submit,
               size=this.props.size or "small",
               js_type="date",
               fluid=this.props.fluid)

    else:
        items = []
        if this.props.text:
            items.append(this.props.text)
            items.append(e(ui.Label.Detail, date))
        else:
            items.append(date)

        clsname = ""
        if utils.defined_or(this.props.disabled, False):
            clsname += " disabled"

        el = e(ui.Label, *items, onClick=this.on_click if this.props.edit_mode and not this.props.disabled else this.toggle, as_="a", className=clsname)

    return el


DateLabel = createReactClass({
    'displayName': 'DateLabel',

    'getInitialState': lambda: {'toggled': False,
                                'edit_mode': False,
                                'data': None,
                                },

    'toggle': lambda: this.setState({'toggled': not this.state.toggled}),
    'on_click': lambda: this.setState({'edit_mode': True}),
    'update_data': utils.update_data,
    'on_submit': datelbl_update,
    'on_change': lambda e, d: this.setState({'data': utils.moment(d.value, "YYYY-MM-DD").unix()}),

    'render': datelbl_render,
}, pure=True)

def update_url(value, id):
    data = this.props.data or this.state.data
    t = utils.lodash_find(data, lambda v, i, c: v['id']==id)
    if t:
        t.js_name = value
        this.update_data(data)

def update_new_url(value, id):
    data = this.props.data or this.state.data
    t = this.state.new_item[id]
    if t:
        t.js_name = value
        n_data = utils.JSONCopy(this.state.new_item)
        this.setState({'new_item': n_data})
        this.update_data(data, new_item=n_data, only_new_data=True)

def remove_url(e, d):
    e.preventDefault()
    tid = e.target.dataset.id
    data = this.props.data or this.state.data
    if tid and data:
        ndata = utils.remove_from_list(data, {'id': tid})
        this.update_data(ndata)

def remove_new_url(e, d):
    tid = e.target.dataset.id
    data = this.props.data or this.state.data
    t = this.state.new_item[tid]
    if t:
        this.state.new_item.remove(t)
        n_data = utils.JSONCopy(this.state.new_item)
        this.setState({'new_item': n_data})
        this.update_data(data, new_item=n_data, only_new_data=True)

def urls_update(p_p, p_s):
    if any((
        p_p.edit_mode != this.props.edit_mode,
    )):
        this.setState({'new_item': []})

def urls_render():
    data = this.props.data or this.state.data

    els = []

    if data:
        for u in data:
            if this.props.edit_mode:
                u_el = e(EditText,
                                    defaultValue=u.js_name,
                                    edit_mode=this.props.edit_mode,
                                    update_data=this.on_update,
                                    data_id=u.id,
                                    fluid=True)
            else:
                u_el = h("a", u.js_name, href=u.js_name, target="_blank")
            els.append(e(ui.List.Item,
                         e(ui.List.Icon, js_name="external share") if not this.props.edit_mode else \
                                e(ui.List.Icon, js_name="remove", onClick=this.on_remove, link=True, **{'data-id': u.id}),
                         e(ui.List.Content,
                            u_el,
                            className="fullwidth",
                           ),
                        key=u.id)
                        )

    if this.state.new_item:
        for uid, u in enumerate(this.state.new_item):
            u_el = e(EditText,
                        defaultOpen=True,
                        defaultValue=u.js_name,
                        edit_mode=this.props.edit_mode,
                        update_data=this.on_update_new,
                        data_id=uid,
                        fluid=True)
            els.append(e(ui.List.Item,
                         e(ui.List.Icon, js_name="remove", onClick=this.on_remove_new, link=True, **{'data-id': uid}),
                         e(ui.List.Content,
                            u_el,
                            className="fullwidth",
                           ),
                        key=uid)
                        )

    if this.props.edit_mode:
        els.append(e(ui.List.Item,
                         e(ui.List.Icon, js_name="plus", onClick=this.on_create_item, color="green", link=True),
                    key="new")
                    )

    return e(ui.List,
             this.props.children if this.props.children else els,
             size=this.props.size,
             relaxed=this.props.relaxed,
             className=this.props.className,
             as_=this.props.as_)

URLs = createReactClass({
    'displayName': 'URLs',

    'getInitialState': lambda: {
                                'data': this.props.data or [],
                                'new_item': []
                                },
    'on_update_new': update_new_url,
    'on_update': update_url,
    'on_create_item': lambda: all((this.state.new_item.append({}), this.setState({'new_item': utils.JSONCopy(this.state.new_item)}))),
    'update_data': utils.update_data,
    'on_remove': remove_url,
    'on_remove_new': remove_new_url,
    'componentDidUpdate': urls_update,
    'render': urls_render
})