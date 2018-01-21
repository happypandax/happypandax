__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui
from src.i18n import tr
from src.propsviews import tagpropsview

__pragma__("tconv")

def taglbl_render():
    ns = this.props.namespace or this.state.namespace or ""
    tag = this.props.tag or this.state.tag or ""
    fav = 0
    description = ""
    if tag:
        description = tr(this, "tag.{}".format(tag), "")

    if ns == "__namespace__":
        ns = ""

    show_ns = this.props.show_ns or this.props.show_ns and ns

    lbl_args = []
    if show_ns and ns:
        lbl_args.append("{}:".format(ns))
        lbl_args.append(e(ui.Label.Detail, tag))
    else:
        lbl_args.append(tag)
    

    #if fav:
    #    lbl_args['icon'] = "star"
    #e(ui.Rating, icon="heart", size="massive", rating=fav)

    el = e(ui.Popup,
           e(tagpropsview.TagProps, tag=tag, namespace=ns, data=this.state.data, id=this.state.id),
            trigger=e(ui.Label,
                    *lbl_args,
                    as_="a",
                    size=this.props.size,
                    ),
            hoverable=True,
            on="click",
            hideOnScroll=True,
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
})
