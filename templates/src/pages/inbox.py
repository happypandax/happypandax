from src.react_utils import (e,
                             createReactClass)
from src.i18n import tr
from src.client import ViewType
from src.ui import TitleChange
from src import pages
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def page_render():
    return [e(TitleChange, title=tr(this, "ui.mi-inbox", "Inbox"), key=1),
            e(pages.ItemViewPage, view_type=ViewType.Inbox,
              history=this.props.history,
              location=this.props.location,
              key=2)]


Page = createReactClass({
    'displayName': 'InboxPage',

    'render': page_render
})
