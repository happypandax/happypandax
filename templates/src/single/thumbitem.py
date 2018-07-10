from src.react_utils import (e, h,
                             createReactClass,
                             )
from src.ui import ui
from src.client import Command, client
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
__pragma__('noskip')


def thumbnail_on_update(p_props, p_state):
    if any((
        p_props.item_type != this.props.item_type,
        p_props.item_id != this.props.item_id,
        p_props.size_type != this.props.size_type,
    )):
        if not (p_props.img != this.props.img) or not this.props.img:
            this.get_thumb()

    if p_props.img != this.props.img:
        this.setState({'img': this.props.img})


__pragma__('tconv')


def thumbnail_get_thumb(data=None, error=None):
    if not this.mounted:
        return
    if data is not None and not error:
        cmd_id = data[str(this.props.item_id)]
        if cmd_id:
            cmd = Command(cmd_id)
            this.setState({'active_cmd': cmd})
            cmd.set_callback(this.set_thumb)
            cmd.poll_until_complete(500)
    elif error:
        pass
    else:
        if this.state.active_cmd:
            this.state.active_cmd.stop()
            this.setState({'active_cmd': None})
        if this.props.item_id and this.props.size_type and this.props.item_type:
            client.call_func("get_image", this.get_thumb,
                             item_ids=[this.props.item_id],
                             size=this.props.size_type, url=True, uri=True, item_type=this.props.item_type)
            s = {'loading': True}
            if this.state.placeholder:
                s['img'] = this.state.placeholder
            this.setState(s)


__pragma__('notconv')


def thumbnail_set_thumb(cmd):
    val = cmd.get_value()
    im = None
    if val:
        im = val['data']
    if not im:
        im = "/static/img/no-image.png"
    if this.is_mounted:
        this.setState({'img': im, 'loading': False, 'active_cmd': None})


def thumbnail_did_mount():
    this.is_mounted = True
    if not this.props.img:
        this.get_thumb()


def thumbnail_will_unmount():
    this.is_mounted = False
    if this.state.active_cmd:
        this.state.active_cmd.stop()


def thumbnail_render():
    img_url = this.state.placeholder
    if this.state.img:
        img_url = this.state.img
    fluid = True
    if this.props.fluid != js_undefined:
        fluid = this.props.fluid

    if this.props.size:
        fluid = False  # can't be defined together

    ex = this.props.kwargs if utils.defined(this.props.kwargs) else {}

    clsname = ""
    if this.props.blur:
        clsname = "blur"
    if this.props.className:
        clsname += ' ' + this.props.className

    el = e(ui.Image, src=img_url,
           fluid=fluid,
           size=this.props.size,
           disabled=this.props.disabled,
           centered=this.props.centered,
           bordered=this.props.bordered,
           rounded=this.props.rounded,
           avatar=this.props.avatar,
           dimmer=this.props.dimmer,
           height=this.props.height,
           as_=this.props.as_,
           href=this.props.href,
           hidden=this.props.hidden,
           shape=this.props.shape,
           spaced=this.props.spaced,
           ui=this.props.ui,
           verticalAlign=this.props.verticalAlign,
           width=this.props.width,
           style=this.props.style,
           className=clsname,
           **ex
           )
    return h("div", e(ui.Dimmer, e(ui.Loader), active=this.state.loading, inverted=True),
             el,
             )


Thumbnail = createReactClass({
    'displayName': 'Thumbnail',

    'is_mounted': False,

    'getInitialState': lambda: {'img': this.props.img or "/static/img/default.png",
                                'loading': False if this.props.img else True,
                                'placeholder': this.props.placeholder if utils.defined(this.props.placeholder) else "/static/img/default.png",
                                'active_cmd': None,
                                },

    'get_thumb': thumbnail_get_thumb,

    'set_thumb': thumbnail_set_thumb,

    'componentDidMount': thumbnail_did_mount,
    'componentWillUnmount': thumbnail_will_unmount,
    'componentDidUpdate': thumbnail_on_update,

    'render': thumbnail_render
}, pure=True)
