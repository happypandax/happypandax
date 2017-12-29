__pragma__('alias', 'as_', 'as')
PinchView = require("react-pinch-zoom-pan")
import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             )
from src.ui import ui
from src.client import Command, client
from src.state import state
from src import utils


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
    this.setState({'img': im, 'loading': False, 'active_cmd': None})


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

    el = e(ui.Image, src=img_url,
           fluid=fluid,
           size=this.props.size,
           disabled=this.props.disabled,
           centered=this.props.centered,
           bordered=this.props.bordered,
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
           **ex
           )
    return e(ui.Segment, e(ui.Dimmer, e(ui.Loader), active=this.state.loading, inverted=True),
             el,
             basic=True,
             className="no-padding-segment",
             inverted=this.props.inverted,
             )


Thumbnail = createReactClass({
    'displayName': 'Thumbnail',

    'getInitialState': lambda: {'img': this.props.img or "",
                                'loading': false if this.props.img else True,
                                'placeholder': this.props.placeholder if utils.defined(this.props.placeholder) else "/static/img/default.png",
                                'active_cmd': None,
                                },

    'get_thumb': thumbnail_get_thumb,

    'set_thumb': thumbnail_set_thumb,

    'componentDidMount': lambda: this.get_thumb() if not this.props.img else None,
    'componentWillUnmount': lambda: this.state.active_cmd.stop if this.state.active_cmd else None,
    'componentDidUpdate': thumbnail_on_update,

    'render': thumbnail_render
})
