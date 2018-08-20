from src import utils
from src.react_utils import (e,
                             createReactClass)
from src.ui import ui
from src.propsviews import artistpropsview
from src.single import circleitem
from src.client import ItemType, client

from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')


def update_metatags(mtags):
    if this.state.data:
        client.call_func("update_metatags", None, item_type=this.state.item_type,
                         item_id=this.state.data.id, metatags=mtags)
        d = this.props.data or this.state.data
        d.metatags = dict(d.metatags)
        d.metatags.update(mtags)
        d = utils.JSONCopy(d)
        this.setState({'data': d})


def item_favorite(e, d):
    e.preventDefault()
    # if this.props.edit_mode:
    #    this.update_data(bool(d.rating), "metatags.favorite")
    # else:
    this.update_metatags({'favorite': bool(d.rating)})


def artistlbl_render():
    name = ""
    fav = 0
    data = this.props.data or this.state.data
    if data:
        if data.preferred_name:
            name = data.preferred_name.js_name
        elif data.names and len(data.names):
            name = data.names[0].js_name

        if data.metatags:
            if data.metatags.favorite:
                fav = 1

    trigger_el = e(ui.Label,
                   e(ui.Icon, js_name="heart outline") if fav else None,
                   e(ui.Icon, js_name="user"),
                   name,
                   e(ui.Icon, js_name="delete",
                     color=this.props.color,
                     link=True,
                     onClick=this.props.onRemove,
                     **{'data-id': data.id, 'data-name': name}) if this.props.edit_mode or this.props.showRemove else None,
                   basic=True,
                   color="blue",
                   as_="a",
                   )

    a_props_el = e(artistpropsview.ArtistProps,
                   data=data,
                   update_data=this.update_data,
                   tags=this.props.tags or this.state.tags,
                   edit_mode=this.props.edit_mode,
                   on_favorite=this.favorite,
                   on_tags=this.on_tags)

    if this.props.edit_mode:
        el = e(ui.Modal,
               e(ui.Modal.Content, a_props_el),
               trigger=trigger_el,
               dimmer="inverted",
               size="small",
               closeOnDocumentClick=True,
               centered=False,
               closeIcon=True,
               )
    else:
        el = e(ui.Popup,
               a_props_el,
               trigger=trigger_el,
               hoverable=True,
               hideOnScroll=True,
               wide="very",
               size="small",
               on="click",
               position="top center"
               )

    return el


__pragma__("notconv")

ArtistLabel = createReactClass({
    'displayName': 'ArtistLabel',

    'getInitialState': lambda: {
        'id': this.props.id,
        'data': this.props.data,
        'tags': this.props.tags,
        'item_type': ItemType.Artist,
    },

    'update_data': utils.update_data,

    'on_tags': lambda d: this.setState({"tags": d}),

    'update_metatags': update_metatags,

    'get_tags': artistpropsview.get_tags,

    'favorite': item_favorite,

    # 'componentDidMount': lambda: this.get_tags() if not utils.defined(this.props.tags) else None,

    'render': artistlbl_render
}, pure=True)


def artistitem_render():
    name = ""
    fav = 0
    data = this.props.data or this.state.data
    circles = []
    if data:
        if data.preferred_name:
            name = data.preferred_name.js_name
        if data.metatags:
            if data.metatags.favorite:
                fav = 1
        circle_ids = []
        if data.circles:
            for c in data.circles:
                if c.id in circle_ids:
                    continue
                circles.append(c)
                circle_ids.append(c.id)

    el_kwargs = {'active': this.props.active}
    el = e(this.props.as_ if this.props.as_ else ui.List.Item,
           e(ui.List.Content,
             e(ui.Rating, icon="heart", size="massive", rating=fav, onRate=this.favorite),
             floated="left",
             ),
           e(ui.List.Content,
             e(ui.Label.Group, [e(circleitem.CircleLabel, data=x, key=x) for x in circles]),
             floated="right",
             ),
           e(ui.Icon, js_name="user circle", size="big", disabled=True),
           e(ui.List.Content,
             e(ui.Header, name, size="tiny"),
             ),
           className=this.props.className,
           onClick=this.on_click,
           **el_kwargs if not this.props.as_ else None
           )

    if not this.props.selection:
        el = e(ui.Popup,
               e(artistpropsview.ArtistProps,
                   data=data,
                   tags=this.props.tags or this.state.tags,
                   edit_mode=this.props.edit_mode,
                   on_favorite=this.favorite,
                   on_tags=this.on_tags),
               trigger=el,
               hoverable=True,
               hideOnScroll=True,
               wide="very",
               on="click",
               position="top center"
               )

    return el


ArtistItem = createReactClass({
    'displayName': 'ArtistItem',

    'getInitialState': lambda: {
        'id': this.props.id,
        'data': this.props.data,
        'tags': this.props.tags,
        'item_type': ItemType.Artist,
    },

    'update_data': utils.update_data,

    'on_tags': lambda d: this.setState({"tags": d}),

    'on_click': lambda e, d: all((this.props.onClick(e, this.props.data or this.state.data) if this.props.onClick else None,)),

    'update_metatags': update_metatags,

    'favorite': item_favorite,


    'render': artistitem_render
}, pure=True)
