from src.react_utils import (e,
                             createReactClass)
from src import utils
from src.ui import ui
from src.single import circleitem
from src.selectors import circleselector
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def on_new_circle(e, data):
    for a in data:
        this.update_data(a, op="append")


def remove_circle(e, d):
    e.preventDefault()
    tid = e.target.dataset.id
    tname = e.target.dataset.js_name
    data = this.props.data or this.state.data
    if tid and data:
        tid = int(tid)
        ndata = utils.remove_from_list(data, tid, key="id")
        this.update_data(ndata)
    if tname and data:
        ndata = utils.remove_from_list(data, tname, key="name")
        this.update_data(ndata)


def circles_render():
    data = this.props.data or this.state.data

    els = []
    if data:
        for a in sorted(data, key=lambda x: utils.get_object_value('name')):
            els.append(e(circleitem.CircleLabel,
                         data=a,
                         key=a.id or utils.get_object_value('name', a) or utils.get_object_value('name', a),
                         edit_mode=this.props.edit_mode,
                         update_data=this.update_data,
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
                       as_=circleselector.CircleSelector),
                     trigger=e(
                         ui.Icon,
                         onClick=this.on_modal_toggle,
                         size="small",
                         link=True,
                         js_name="plus",
                         color="teal"),
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


Circles = createReactClass({
    'displayName': 'Circles',

    'getInitialState': lambda: {
        'data': this.props.data or [],
        'modal_open': False,
    },
    'on_new_parody': on_new_circle,
    'on_click': lambda: this.setState({'edit_mode': True}),
    'on_modal_toggle': lambda: this.setState({'modal_open': not this.state.modal_open}),
    'on_remove': remove_circle,
    'update_data': utils.update_data,
    'render': circles_render
})
