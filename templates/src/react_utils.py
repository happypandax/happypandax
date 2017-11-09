import utils
from state import state

React = require("react")
ReactDOM = require("react-dom")
createReactClass = require('create-react-class')
Router = require("react-router-dom").BrowserRouter
Link = require("react-router-dom").Link
NavLink = require("react-router-dom").NavLink
Route = require("react-router-dom").Route
withRouter = require("react-router").withRouter

__pragma__("kwargs")
def e(elm_type, *args, **props):
    props.pop("constructor")
    return React.createElement(elm_type, props, *args)
__pragma__("nokwargs")

__pragma__("kwargs")
def h(elm_type, *args, **props):
    return e(elm_type, *args, **props)
__pragma__("nokwargs")


def render(react_element, destination_id, callback=lambda: None):
    container = document.getElementById(destination_id)
    ReactDOM.render(react_element, container, callback)

__pragma__("jsiter")
def QueryLink(props):
    to_obj = {'pathname': location.pathname}

    if isinstance(props.to, str):
        to_obj.pathname = props.to
    elif props.to:
        to_obj = props.to

    query = dict()
    if props.keep_search or props.keep_search == js_undefined:
        query.update(utils.query_to_obj(location.search))

    if props.query:
        query.update(props.query)

    to_obj['search'] = utils.query_to_string(query)

    return e(Link, *props.children, to={'pathname':to_obj.pathname, 'search':to_obj.search, 'hash':to_obj.hash, 'state':to_obj.state}, js_replace=props.js_replace,
             className=props.className, onClick=props.onClick)
__pragma__("nojsiter")

def scrolltotop_update(p_props):
    if this.props.location != p_props.location:
        if state.container_ref:
            state.container_ref.scrollTop = 0
        else:
            window.scrollTo(0,0)

ScrollToTop = withRouter(createReactClass({
    'displayName': 'ScrollToTop',

    'componentDidUpdate': scrolltotop_update,

    'render': lambda: this.props.children
}))
