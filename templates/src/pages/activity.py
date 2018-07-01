from src.react_utils import (e,
                             createReactClass)
from src.i18n import tr
from src.ui import ui, TitleChange, TR
from src.client import client, ProgressType
from src.state import state
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')
__pragma__('alias', 'js_input', 'input')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def get_progress(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data})
    elif error:
        state.app.notif("Failed to retrieve progress update", level="warning")
    else:
        if state['active'] and state['connected'] and state['accepted']:
            client.call_func("get_command_progress", this.get_progress)


def page_mount():
    this.get_progress()
    this.interval_func = setInterval(this.get_progress, 1300)


def page_render():

    els = []

    special_type = (ProgressType.CheckUpdate,
                    ProgressType.UpdateApplication)

    for p in this.state.data:
        if p['type'] == ProgressType.Unknown:
            continue
        p_title = p.title
        kwargs = {}
        kwargs['progress'] = 'percent'
        if p['type'] in special_type or p['subtype'] in special_type:
            kwargs['color'] = 'blue'
        if p['max']:
            kwargs['value'] = p['value']
            kwargs['total'] = p['max']
            kwargs['autoSuccess'] = True
        else:
            kwargs['percent'] = 99
            kwargs['autoSuccess'] = False

        els.append(e(ui.List.Item,
                     e(ui.List.Content,
                       e(ui.List.Header, p_title),
                       e(ui.Progress, *([p.subtitle] if p.subtitle else []),
                         precision=2,
                         indicating=True,
                         active=True,
                         **kwargs),
                       e(ui.List.Description,
                         e(ui.List,
                           e(ui.List.Item, e(ui.List.Content, utils.moment.unix(p.timestamp).fromNow())),
                           e(ui.List.Item, e(ui.List.Content, p.text)),
                           horizontal=True,
                           divided=True,
                           ),
                         className="sub-text"),
                       )
                     ))

    return e(ui.Container,
             e(TitleChange, title=tr(this, "ui.mi-activity", "Activity")),
             e(ui.Form,
               e(ui.Form.Group,
                 e(ui.Form.Input,
                   width=16,
                   fluid=True,
                   action={'color': 'teal', 'icon': 'download'}),
                 placeholder=tr(this, "", "Click to see supported URLs"),
                 ),
               ),
             e(ui.Divider, section=True),
             e(ui.List,
               *els,
               selection=True,
               relaxed="very",
               divided=True,
               animated=True,
               ),
             )


Page = createReactClass({
    'displayName': 'ActivityPage',
    'interval_func': None,

    'componentWillMount': lambda: this.props.menu([
        e(ui.Menu.Item, e(TR, "ui.mi-batch-urls", default="Batch URLs")),
    ]),
    'componentDidMount': page_mount,
    'componentWillUnmount': lambda: clearInterval(this.interval_func) if this.interval_func else None,

    'getInitialState': lambda: {
        'data': [],
    },

    'get_progress': get_progress,


    'render': page_render
})
