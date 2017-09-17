import utils

React = require("react")
ReactDOM = require("react-dom")
createReactClass = require('create-react-class')
Router = require("react-router-dom").BrowserRouter
Link = require("react-router-dom").Link
Route = require("react-router-dom").Route
LazyLoad = require("react-lazyload")['default']

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
    if isinstance(props.to, str):
        obj = {'pathname': props.to},
    elif props.to:
        obj = props.to
    else:
        obj = {}
    if location.search:
        if props.query:
            props.query.update(utils.query_string.parse(props.query))
    obj['search'] = utils.query_string.stringify(props.query)

    return e(Link, to={'pathname':obj.pathname, 'search':obj.search, 'hash':obj.hash, 'state':obj.state}, replace=props.replace)
__pragma__("nojsiter")
