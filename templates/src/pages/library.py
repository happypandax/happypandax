from src.react_utils import (h,
                             e,
                             React,
                             createReactClass)
from src.ui import ui
from src.i18n import tr
from src.state import state
from src.client import ViewType
from src import pages
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def page_render():
    return e(pages.ItemViewPage,
             view_type=ViewType.Library,
             history=this.props.history,
             location=this.props.location)


Page = createReactClass({
    'displayName': 'LibraryPage',

    'render': page_render
})
