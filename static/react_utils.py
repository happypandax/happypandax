React = require("react")
ReactDOM = require("react-dom")
createReactClass = require('create-react-class')

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

