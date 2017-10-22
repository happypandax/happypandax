__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass)
from ui import ui
from client import client, ServerMsg
from i18n import tr
import utils


def set_key(e):
    this.setState({'key':e.target.value})
    this.props.on_change(this.props.idx, (e.target.value, this.state['value']))

def get_type(s):
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1]
        d = {}
        kv = []
        sp = s.split(':')
        for v in sp:
            if len(kv) == 2:
                d[kv[0]] = kv[1]
                kv.clear()
            kv.append(get_type(v))

        if len(kv) == 2:
            d[kv[0]] = kv[1]
        return d

    # starwith and endswith doesn't work with tuple, transcrypt fault
    elif s[0] in ("'", '"') and s[len(s) - 1] in ("'", '"'):
        return s[1:-1]
    elif s.lower() in ('none', 'null'):
        return None
    elif s.lower() == "true":
        return True
    elif s.lower() == "false":
        return False
    else:
        try:
            return int(s)
        except ValueError:
            return s

def set_value(e):
    value = e.target.value
    value = value.strip()
    if value.startswith('[') and value.endswith(']'):
        value = [
            get_type(x.strip()) for x in value.replace(
                '[', '').replace(
                ']', '').split(',') if x]

    if isinstance(value, str):
        value = get_type(value)
    this.setState({'value':value})
    this.props.on_change(this.props.idx, (this.state['key'], value))

ApiKwarg = createReactClass({
    'displayName': 'ApiKwarg',

    'getInitialState': lambda: {
        "key":"",
        "value":"",
        },

    'set_key': set_key,
    'set_value': set_value,

    'render': lambda: e(ui.Form.Group,
                        e(ui.Form.Input, js_name="param", label=tr(this, "", "Parameter"), onChange=this.set_key, inline=True, width="6"),
                        e(ui.Form.Input, js_name="value", label=tr(this, "", "Value"), onChange=this.set_value, inline=True, width="10"),
                        )
})

def handle_submit(ev):
    ev.preventDefault()
    this.setState({'calling':True})
    serv_data = {
        'fname': this.state['func_name']
        }

    def serv_rsponse(ctx, d, err):
        ctx.props.from_server(utils.syntax_highlight(JSON.stringify(d, None, 4)))
        ctx.setState({'calling':False})

    serv_data.update(this.state['kwargs'])
    msg = client.call(ServerMsg([serv_data], serv_rsponse, contextobj=this))
    this.props.to_server(utils.syntax_highlight(JSON.stringify(msg._msg['msg'], None, 4)))

__pragma__("jsiter")
def set_kwargs(i, v):
    k = {}
    this.state['params'][i] = v
    for i in this.state['params']:
        kv = this.state['params'][i]
        if kv[0].strip():
            k[kv[0]] = kv[1]

    this.setState({'kwargs':k})
__pragma__("nojsiter")


ApiForm = createReactClass({
    'displayName': 'ApiForm',

    'getInitialState': lambda: {
        "input_count":1,
        "func_name":"",
        "params":{},
        "kwargs":{},
        "calling":False,
        },

    'set_func_name': lambda e: this.setState({'func_name':e.target.value}),

    'add_kwarg': lambda e, v: this.setState({'input_count':this.state['input_count']+1}),

    'set_kwargs': set_kwargs,

    'render_kwargs': lambda t: [e(ApiKwarg, idx=x, on_change=t.set_kwargs) for x in range(t.state['input_count'])],

    'handle_submit': handle_submit,

    'render': lambda: e(ui.Form,
                        e(ui.Form.Input, label=tr(this, "", "Function"), onChange=this.set_func_name),
                        *this.render_kwargs(this),
                        e(ui.Form.Group,
                            e(ui.Button, content=tr(this, "", "Add parameter"), onClick=this.add_kwarg),
                            e(ui.Form.Button, tr(this, "", "Call function",), loading=this.state['calling']),
                            ),
                        onSubmit=this.handle_submit
                        )
})

def formatted_json(msg):
    return h('pre', dangerouslySetInnerHTML={'__html':msg})

Page = createReactClass({
    'displayName': 'ApiPage',

    'getInitialState': lambda: {
        "to_server":"",
        "from_server":"",},

    'componentWillMount': lambda: this.props.menu(None),

    'set_msg_to': lambda msg: this.setState({'to_server':msg}),
    'set_msg_from': lambda msg: this.setState({'from_server':msg}),

    'render': lambda: e(ui.Container, e(ui.Grid.Column,
                        e(ui.Message,
                          e(ui.Message.Header, tr(this, "ui.h-server-comm", "Server Communication")),
                          h(ui.Message.Content, tr(this, "ui.t-server-comm-tutorial", "..."), as_="pre"),
                          info=True,
                          ),
                        e(ui.Divider),
                        e(ApiForm, to_server=this.set_msg_to, from_server=this.set_msg_from),
                        e(ui.Divider),
                        e(ui.Accordion,
                          panels=[
                              {'key':0, 'title':tr(this, "", "Message"), 'content':e(ui.Message, formatted_json(this.state['to_server']), className="overflow-auto")},
                              {'key':1, 'title':tr(this, "", "Response"), 'content':e(ui.Message, formatted_json(this.state['from_server']), className="overflow-auto")},
                              ],
                          exclusive=False,
                          defaultActiveIndex=[0, 1]
                          )
                        ))
})
