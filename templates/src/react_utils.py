from src.state import state
from src import utils
from org.transcrypt.stubs.browser import __pragma__

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Date = None
__pragma__('noskip')

React = require("react")
ReactDOM = require("react-dom")
createReactClass_ = require('create-react-class')
shallowCompare = require('react-addons-shallow-compare')
Router = require("react-router-dom").BrowserRouter
Link = require("react-router-dom").Link
NavLink = require("react-router-dom").NavLink
Route = require("react-router-dom").Route
Prompt = require("react-router-dom").Prompt
Switch = require("react-router-dom").Switch
withRouter = require("react-router").withRouter
Redirect = require("react-router-dom").Redirect

__pragma__("kwargs")


def createReactClass(obj, pure=True):
    if pure and not obj.shouldComponentUpdate:
        obj['shouldComponentUpdate'] = lambda np, ns: shallowCompare(this, np, ns)

    obj['real_cmpmount'] = obj['componentWillMount']
    obj['real_cmpunmount'] = obj['componentWillUnmount']

    def cmp_mount():
        this.mounted = True
        if this.real_cmpmount:
            this.real_cmpmount()

    def cmp_unmount():
        this.mounted = False
        if this.real_cmpunmount:
            this.real_cmpunmount()

    obj['componentWillMount'] = cmp_mount
    obj['componentWillUnmount'] = cmp_unmount

    return createReactClass_(obj)


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

    c = props.children if utils.defined(props.children) else []

    return e(Link, *c, to={'pathname': to_obj.pathname, 'search': to_obj.search, 'hash': to_obj.hash, 'state': to_obj.state}, js_replace=props.js_replace,
             className=props.className, onClick=props.onClick)


__pragma__("nojsiter")


def scrolltotop_update(p_props):
    if this.props.location != p_props.location:
        if state.container_ref:
            utils.scroll_to_element(state.container_ref)
        else:
            utils.scroll_to_element(window)


ScrollToTop = withRouter(createReactClass({
    'displayName': 'ScrollToTop',

    'componentDidUpdate': scrolltotop_update,

    'render': lambda: this.props.children
}))
