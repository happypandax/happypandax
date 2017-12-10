__pragma__('alias', 'as_', 'as')
from src.react_utils import (h,
                             e,
                             React,
                             createReactClass)
from src.ui import ui
from src.client import client
from src.i18n import tr
from src.state import state
from src import item, utils

Page = createReactClass({
    'displayName': 'DirectoryPage',

    'componentWillMount': lambda: this.props.menu([
        e(ui.Menu.Item, js_name=tr(this, "", "Artists")),
        e(ui.Menu.Item, js_name=tr(this, "", "Tags")),
    ]),

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Segment,
                        )
})
