from src import utils
from src.react_utils import (e,
                             Link,
                             createReactClass)
from src.ui import ui
from src.i18n import tr
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

__pragma__("tconv")


def parodyprops_render():
    url_search_query = {'search': ''}
    if this.state.data and this.state.data.names:
        url_search_query = {'search': 'parody:"{}"'.format(this.state.data.names[0].js_name)}

    return e(ui.Button.Group,
             e(ui.Button, icon="grid layout", title=tr(this, "ui.t-show-galleries", "Show galleries"),
               as_=Link, to=utils.build_url("/library", query=url_search_query, keep_query=False)),
             e(ui.Button, icon="heart", title=tr(this, "ui.t-show-fav-galleries", "Show favorite galleries"),
               as_=Link, to=utils.build_url("/favorite", query=url_search_query, keep_query=False)),
             basic=True,
             size=this.props.size or "tiny",
             className=this.props.ClassName,
             )


__pragma__("notconv")

ParodyProps = createReactClass({
    'displayName': 'ParodyProps',

    'getInitialState': lambda: {
        'data': this.props.data,
        'id': this.props.id,
    },

    'render': parodyprops_render
})
