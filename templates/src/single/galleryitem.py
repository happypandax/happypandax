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

def gallery_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


def gallery_render():
    fav = 0
    title = ""
    rating = 0
    artists = []
    item_id = this.state.id
    if this.state.data:
        rating = this.state.data.rating
        title = this.state.data.titles[0].js_name
        if this.state.data.metatags.favorite:
            fav = 1
        if not item_id:
            item_id = this.state.data.id

        for a in this.state.data.artists:
            if len(a.names) > 0:
                artists.append(a.names[0].js_name)

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
        thumb = e(Link, thumb, to={'pathname': '/item/gallery',
                                   'search': utils.query_to_string({'id': item_id})})

    return e(ui.Card,
             h("div",
               thumb,
               e(ui.Rating, icon="heart", size="massive", className="card-item top left", rating=fav),
               e(ui.Popup,
                 e(ui.Rating, icon="star", defaultRating=rating, maxRating=10, clearable=True),
                 trigger=e(
                     ui.Label,
                     rating,
                     className="card-item bottom left",
                     size="large",
                     color="yellow",
                     as_="a"),
                   hoverable=True,
                   on="click",
                   hideOnScroll=True,
                   position="left center"
                 ),
                 e(ui.Icon, js_name="ellipsis vertical", bordered=True,
                   className="card-item bottom right", link=True, inverted=True),
               className="card-content",
               ),
             e(ui.Popup,
               trigger=e(ui.Card.Content,
                         e(ui.Card.Header, title, className="text-ellipsis card-header"),
                         e(ui.Card.Meta, *[h("span", x) for x in artists], className="text-ellipsis"),),
               header=title,
               content=h("div", *[h("span", x) for x in artists]),
               hideOnScroll=True,
               hoverable=False,
               position="bottom center"
               ),
             className=add_cls,
             link=True)

Gallery = createReactClass({
    'displayName': 'Gallery',

    'getInitialState': lambda: {'id': None,
                                'data': this.props.data,
                                'item_type': ItemType.Gallery,
                                },

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': gallery_on_update,

    'render': gallery_render
})