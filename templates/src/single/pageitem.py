__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
from src.ui import ui
from src.client import (ItemType, ImageSize, client)
from src.state import state
from src.single import thumbitem
from src import utils

__pragma__("tconv")


def open_external():
    if this.state.data:
        client.call_func("open_gallery", None, item_id=this.state.data.id, item_type=this.state.item_type)


__pragma__("notconv")


def page_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


def page_render():
    fav = 0
    title = ""
    item_id = this.state.id
    number = 0
    if this.state.data:
        title = str(this.state.data.number)
        number = this.state.data.number
        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id

    add_cls = this.props.className or ""

    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    thumb_kwargs = {}
    if this.props.external_viewer:
        thumb_kwargs['onClick'] = this.open_external
    thumb = e(thumbitem.Thumbnail,
              item_id=item_id,
              item_type=this.state.item_type,
              size_type=ImageSize.Medium,
              centered=True,
              size=this.props.size,
              kwargs=thumb_kwargs,
              )
    if link:
        if not this.props.external_viewer:
            thumb = e(Link, thumb, to={'pathname': '/item/page',
                                       'search': utils.query_to_string({'id': item_id, 'number': number})})

    return e(ui.Card,
             h("div",
               thumb,
               e(ui.Icon, js_name="ellipsis vertical", bordered=True,
                 className="card-item bottom right", link=True, inverted=True),
               className="card-content",
               ),
             e(ui.Card.Content, e(ui.Card.Header, e(ui.Label, title, circular=True), className="text-ellipsis card-header")),
             className=add_cls,
             centered=this.props.centered,
             link=True)


Page = createReactClass({
    'displayName': 'Page',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Page},

    'open_external': open_external,

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': page_on_update,
    'render': page_render
})
