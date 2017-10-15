__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass)
from ui import ui, Slider
from i18n import tr
from state import state
from client import ItemType, ViewType, ImageSize, client
import items
import utils

def PageNav(props):
    els = []
    if props.number > 1:
        els.append(e(ui.Grid.Column, e(ui.Button, icon="arrow left"), onClick=props.prev_page))
    els.append(e(ui.Grid.Column, e(ui.Label, str(props.number)+"/"+str(props.count) if props.count else props.number)))
    if props.number < props.count:
        els.append(e(ui.Grid.Column, e(ui.Button, icon="arrow right"), onClick=props.next_page))

    return e(ui.Grid.Row,
             e(ui.Grid,
               *els,
             container=True,
             textAlign="center",
             verticalAlign="middle"
               )
             )

__pragma__("kwargs")
def get_item(data=None, error=None, go=None):
    if data is not None and not error:
        this.setState({"data":data, "loading":False})
        if this.state.pages is None:
            this.get_pages(gid=data.gallery_id)
    elif error:
        state.app.notif("Failed to fetch item ({})".format(this.state.id), level="error")
    else:
        item = this.state.item_type
        item_id = this.state.id
        if this.state.data:
            item_id = this.state.data.id
        go = go.lower() if go else go

        if item:
            if go in ("next", "prev") or this.state.gid:
                if item_id:
                    client.call_func("get_page", this.get_item, page_id=item_id, prev=go=="prev")
                else:
                    client.call_func("get_page", this.get_item, gallery_id=this.state.gid)
            elif item_id:
                client.call_func("get_item", this.get_item, item_type=item, item_id=item_id)
            this.setState({'loading':True})
__pragma__("nokwargs")
          
__pragma__("kwargs")
def get_pages(data=None, error=None, gid=None):
    if data is not None and not error:
        this.setState({"pages":data['count']})
    elif error:
        state.app.notif("Failed to fetch pages ({})".format(this.state.gid), level="error")
    else:
        item = ItemType.Gallery
        item_id = gid
        if item and item_id:
            client.call_func("get_related_count", this.get_pages, item_type=item, item_id=item_id,
                             related_type=this.state.item_type)
__pragma__("nokwargs")

def on_key(ev):
    if ev.key=="Escape":
        this.back_to_gallery()
    elif ev.key=="ArrowRight":
        this.next_page()
    elif ev.key=="ArrowLeft":
        this.prev_page()

def page_render():
    img_url = this.state.img
    number = 0
    p_id = this.state.id
    if this.state.data:
        p_id = this.state.data.id
        number = this.state.data.number

    if not img_url:
        img_url = "static/img/default.png"

    return e(ui.Grid,
             e(PageNav, prev_page=this.prev_page, next_page=this.next_page, number=number, count=this.state.pages),
             e(ui.Grid.Row, e(ui.Grid.Column,
                              e(items.Thumbnail,
                                item_id=p_id,
                                item_type=this.state.item_type,
                                size_type=ImageSize.Original,
                                centered=True,
                                fluid=False,
                                bordered=True,
                                onClick=this.next_page
                                )),
               centered=True),
             e(PageNav, prev_page=this.prev_page, next_page=this.next_page, number=number, count=this.state.pages),
             e(ui.Grid.Row, e(ui.Grid.Column, e(ui.Segment, as_=ui.Container))),
             padded=True,
             )

Page = createReactClass({
    'displayName': 'Page',

    'getInitialState': lambda: {'id': int(utils.get_query("id", 0)),
                                'gid': int(utils.get_query("gid", 0)),
                                'pages': None,
                                'data':this.props.data,
                                'tag_data':this.props.tag_data or {},
                                'item_type':ItemType.Page,
                                'loading':True,
                                },

    'get_item': get_item,
    'get_pages': get_pages,
    'on_key': on_key,
    'prev_page': lambda: all((utils.go_to(this.props.history, query={'id':this.state.data.id, 'go':"prev"}), this.get_item(go=utils.get_query("go")))),
    'next_page': lambda: all((utils.go_to(this.props.history, query={'id':this.state.data.id, 'go':"next"}), this.get_item(go=utils.get_query("go")))),
    'back_to_gallery': lambda: utils.go_to(this.props.history, "/item/gallery", query={'id':this.state.data.gallery_id}, keep_query=False),

    'componentDidMount': lambda: window.addEventListener("keydown", this.on_key, False),
    'componentWillUnmount': lambda: window.removeEventListener("keydown", this.on_key, False),

    'componentWillMount': lambda: all((this.props.menu([
                                        e(ui.Menu.Menu, e(ui.Menu.Item, icon="arrow up", onClick=this.back_to_gallery)),
                                        ]), 
                                       (this.get_item(go=utils.get_query("go")) if not this.state.data else None),
                                       )),

    'render': page_render
})

