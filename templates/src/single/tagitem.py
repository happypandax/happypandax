__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui

__pragma__("tconv")
def taglbl_render():
    ns = this.props.namespace or this.state.namespace or ""
    tag = this.props.tag or this.state.tag or ""
    fav = 0

    if ns == "__namespace__":
        ns = ""

    show_ns = this.props.show_ns or this.props.show_ns and ns


    lbl_args = []
    if show_ns:
        lbl_args.append("{}:".format(ns))
    lbl_args.append(e(ui.Label.Detail, tag))

    if fav:
        lbl_args['icon'] = "star"
    #e(ui.Rating, icon="heart", size="massive", rating=fav)
    return e(ui.Popup,
                trigger=e(ui.Label,
                    *lbl_args,
                    as_="a",
                    ),
                hoverable=True,
                on="click",
                hideOnScroll=True,
                position="top center"
                )
__pragma__("notconv")

TagLabel = createReactClass({
    'displayName': 'TagLabel',

    'getInitialState': lambda: {
        'namespace': this.props.namespace,
        'tag': this.props.tag,
        'data': this.props.data,
        'id':this.props.id,
        },

    'render': taglbl_render
})