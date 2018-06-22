from src.react_utils import (e,
                             createReactClass)
from src import pages
from src.i18n import tr
from src.ui import TitleChange
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def page_render():
    return [e(TitleChange, title=tr(this, "ui.mi-browse", "Browse"), key=1),
            e(pages.ItemViewPage,
              history=this.props.history,
              location=this.props.location,
              key=2)]


Page = createReactClass({
    'displayName': 'LibraryPage',

    'render': page_render
}, pure=True)
