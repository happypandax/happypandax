from react_utils import (h,
                         e,
                         render,
                         React,
                         ReactDOM,
                         createReactClass)
import ui

App = createReactClass({
    'displayName': 'App',

    'render': lambda: h(ui.Nav)
})

render(e(App), 'root')