__pragma__('alias', 'as_', 'as')
from src.react_utils import (h,
                             e,
                             React,
                             createReactClass)
from src.ui import ui
from src.i18n import tr
from src.state import state
from src.client import ViewType
from src import pages


def page_render():
    return e(pages.ItemViewPage, view_type=ViewType.Inbox, history=this.props.history)


Page = createReactClass({
    'displayName': 'InboxPage',

    'render': page_render
})
