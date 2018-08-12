from src.react_utils import (e,
                             createReactClass)
from src.ui import ui
from src.propsviews import tagpropsview
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
__pragma__('noskip')

__pragma__("tconv")


def taglbl_render():
    ns = this.props.namespace or this.state.namespace or ""
    tag = this.props.tag or this.state.tag or ""
    #fav = 0

    if ns == "__namespace__":
        ns = ""

    show_ns = this.props.show_ns or this.props.show_ns and ns

    lbl_args = []
    if show_ns and ns:
        lbl_args.append("{}:".format(ns))
        lbl_args.append(e(ui.Label.Detail, tag))
    else:
        lbl_args.append(tag)

    # if fav:
    #    lbl_args['icon'] = "star"
    #e(ui.Rating, icon="heart", size="massive", rating=fav)

    el = e(ui.Popup,
           e(tagpropsview.TagProps, tag=tag, namespace=ns, data=this.state.data, id=this.state.id),
           trigger=e(ui.Label,
                     *lbl_args,
                     e(ui.Icon, js_name="delete",
                       color=this.props.color,
                       link=True,
                       onClick=this.props.onRemove,
                       **{'data-id': this.props.id, 'data-tag': this.props.tag, 'data-namespace': this.props.namespace or ''}) if this.props.edit_mode else None,
                     as_="a",
                     size=this.props.size,
                     ),
           hoverable=True,
           hideOnScroll=True,
           on="click",
           position="top center",
           wide="very",
           )
    return el


__pragma__("notconv")

TagLabel = createReactClass({
    'displayName': 'TagLabel',

    'getInitialState': lambda: {
        'namespace': this.props.namespace,
        'tag': this.props.tag,
        'data': this.props.data,
        'id': this.props.id,
    },

    'render': taglbl_render
}, pure=True)
