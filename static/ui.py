__pragma__ ('alias', 'as_', 'as')
from react_utils import (h,e,
                        render,
                        React,
                        ReactDOM,
                        createReactClass)

ui = require("semantic-ui-react")

Nav = createReactClass({
    'displayName': 'Nav',

    'getInitialState': lambda: {"visible":True},

    'render': lambda: e(ui.Sidebar,
                        e(ui.Menu.Item, js_name="test"),
                        e(ui.Menu.Item, js_name="test1"),
                        as_=ui.Menu,
                        animation="slide along",
                        width="thin",
                        vertical=True,
                        visible=True)
})
