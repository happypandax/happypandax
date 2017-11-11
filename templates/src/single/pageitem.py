__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
from src.ui import ui
from src.client import (ItemType, ImageSize)
from src.state import state
from src.single import thumbitem
from src import utils

def page_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


def page_render():
    fav = 0
    title = ""
    item_id = this.state.id
    if this.state.data:
        title = str(this.state.data.number)
        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id

    add_cls = this.props.className or ""

    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    thumb = e(thumbitem.Thumbnail,
              item_id=item_id,
              item_type=this.state.item_type,
              size_type=ImageSize.Medium,
              size=this.props.size,
              )
    if link:
        thumb = e(Link, thumb, to={'pathname': '/item/page',
                                   'search': utils.query_to_string({'id': item_id})})

    return e(ui.Card,
             h("div",
               thumb,
               e(ui.Icon, js_name="ellipsis vertical", bordered=True,
                 className="card-item bottom right", link=True, inverted=True),
               className="card-content",
               ),
             e(ui.Card.Content, e(ui.Card.Header, e(ui.Label, title, circular=True), className="text-ellipsis card-header")),
             className=add_cls,
             link=True)

Page = createReactClass({
    'displayName': 'Page',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Page},

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': page_on_update,
    'render': page_render
})