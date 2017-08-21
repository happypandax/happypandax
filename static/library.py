__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         render,
                         React,
                         ReactDOM,
                         createReactClass,
                         Router)
from ui import ui

App = createReactClass({
    'displayName': 'App',

    'getInitialState': lambda: {
        "sidebar_toggled":True,
        "menu_nav_contents":None},

    'toggle_sidebar': lambda: (this.setState({'sidebar_toggled':not this.state['sidebar_toggled']})),

    'render': lambda: e(Router,
                        h("div",
                            e(nav_ui.MenuNav, toggler=this.toggle_sidebar, contents=this.state["menu_nav_contents"]),
                            e(ui.Sidebar.Pushable,
                            e(nav_ui.SideBarNav, toggled=this.state["sidebar_toggled"]),
                            e(ui.Sidebar.Pusher,
                              e(ui.Segment, basic=True)
                            ),
                            as_=ui.Segment,
                            attached="bottom"
                            ),
                            className="bodyheight"
                            )
                        )
})

render(e(App), 'root')