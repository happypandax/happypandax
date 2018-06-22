from src.react_utils import (h,
                             e,
                             createReactClass,
                             Link)
from src.ui import ui
from src.client import (ItemType, ImageSize, client)
from src.single import thumbitem
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
__pragma__('noskip')

__pragma__("tconv")


def open_external():
    if this.state.data:
        client.call_func("open_gallery", None, item_id=this.state.data.id, item_type=this.state.item_type)


__pragma__("notconv")


def page_on_update(p_props, p_state):
    if p_props.data != this.props.data:
        this.setState({'data': this.props.data, 'id': this.props.data.id if this.props.data else None})


def page_on_click(e):
    if this.props.onClick:
        this.props.onClick(e, this.state.data)


def page_render():
    #fav = 0
    title = ""
    item_id = this.state.id
    gallery_id = 0
    number = 0
    if this.state.data:
        title = str(this.state.data.number)
        number = this.state.data.number
        # if this.state.data.metatags.favorite:
        #    fav = 1
        if not item_id:
            item_id = this.state.data.id
        gallery_id = this.state.data.gallery_id

    add_cls = this.props.className or ""

    page_url = '/item/gallery/{}/page/{}'.format(gallery_id, number)

    link = True
    if not this.props.link == js_undefined:
        link = this.props.link

    thumb_kwargs = {}
    if this.props.onClick:
        thumb_kwargs['onClick'] = this.on_click
    if this.props.external_viewer:
        thumb_kwargs['onClick'] = this.open_external
    thumb = e(thumbitem.Thumbnail,
              item_id=item_id,
              item_type=this.state.item_type,
              size_type=this.props.size_type if this.props.size_type else ImageSize.Medium,
              centered=True,
              blur=this.props.blur,
              size=this.props.size,
              kwargs=thumb_kwargs,
              )
    if link:
        if not this.props.external_viewer:
            thumb = e(Link, thumb, to={'pathname': page_url,
                                       })

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
    'on_click': page_on_click,

    'componentWillMount': lambda: this.setState({'id': this.props.data.id if this.props.data else this.state.data.id if this.state.data else None}),
    'componentDidUpdate': page_on_update,
    'render': page_render
}, pure=True)
