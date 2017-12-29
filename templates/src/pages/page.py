__pragma__('alias', 'as_', 'as')
from src.react_utils import (h,
                             e,
                             React,
                             createReactClass,
                             Link)
from src.ui import ui, Slider
from src.i18n import tr
from src.state import state
from src.client import (ItemType, ViewType, ImageSize, client, Command)
from src.single import thumbitem
from src.views import tagview
from src import utils


def PageNav(props):
    els = []
    if props.number > 1:
        els.append(e(ui.Button, icon="arrow left", as_=Link, to=props.p_url))
    els.append(e(ui.Button, str(props.number) + "/" + str(props.count) if props.count else props.number))
    if props.number < props.count:
        els.append(e(ui.Button, icon="arrow right", as_=Link, to=props.n_url))

    return e(ui.Grid.Row,
             e(ui.Grid.Column,
               *els,
               textAlign="center",
               ),
             columns=1
             )


__pragma__("iconv")
__pragma__("tconv")


def set_thumbs(cmd):
    if this.cmd_data and this.state.other:
        values = cmd.get_value()
        d = this.state.other
        for pnumb in d:
            p = d[pnumb]['data']
            d[pnumb]['img'] = values[this.cmd_data[p.id]]['data']
        this.setState({'other': d})


__pragma__("notconv")
__pragma__("noiconv")

__pragma__("kwargs")
__pragma__("iconv")
__pragma__("tconv")


def get_thumbs(data=None, error=None, other=None):
    if data is not None and not error:
        this.cmd_data = data
        cmd = Command(list(dict(data).values()))
        cmd.set_callback(this.set_thumbs)
        cmd.poll_until_complete(500)
    elif error:
        pass
    else:
        if other:
            item_ids = [x.id for x in other]
            client.call_func("get_image", this.get_thumbs,
                                  item_ids=item_ids,
                                  size=ImageSize.Original, url=True, uri=True,
                                  item_type=this.state.item_type)


__pragma__("notconv")
__pragma__("noiconv")
__pragma__("kwargs")


def get_other(data=None, error=None):
    if data is not None and not error:
        pages = {}
        for p in data:
            pages[p.number] = {}
            pages[p.number]['data'] = p
        this.setState({'other': pages})
        this.get_thumbs(other=data)


__pragma__("kwargs")
__pragma__("tconv")
__pragma__("iconv")


def get_item(ctx=None, data=None, error=None, go=None):
    if ctx is not None and not error:
        if data is not None:
            this.setState({"data": data, "loading": False})
            if this.state.pages is None:
                this.get_pages(gid=data.gallery_id)
            if not this.state.other:
                client.call_func("get_related_items",
                                 this.get_other, item_type=ItemType.Gallery,
                                 item_id=data.gallery_id)
    elif error:
        state.app.notif("Failed to fetch item ({})".format(this.state.id), level="error")
    else:
        item = this.state.item_type
        item_id = utils.get_query("id")
        gid = utils.get_query("gid")
        go = go.lower() if go else go

        if this.state.data and this.state.other and go:
            next_numb = this.state.data.number
            next_numb = next_numb - 1 if go == "prev" else next_numb + 1
            if next_numb in this.state.other:
                this.setState({'data': this.state.other[next_numb]['data']})
                return
        if item:
            if go in ("next", "prev") or gid:
                if item_id:
                    client.call_func("get_page", this.get_item, page_id=item_id, prev=go == "prev", ctx=True)
                else:
                    client.call_func("get_page", this.get_item, gallery_id=gid, ctx=True)
            elif item_id:
                client.call_func("get_item", this.get_item, item_type=item, item_id=item_id, ctx=True)
            this.setState({'loading': True})


__pragma__("noiconv")
__pragma__("notconv")
__pragma__("nokwargs")

__pragma__("kwargs")


def get_pages(data=None, error=None, gid=None):
    if data is not None and not error:
        this.setState({"pages": data['count']})
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
    if ev.key == "Escape":
        this.back_to_gallery()
    elif ev.key == "ArrowRight":
        this.next_page(ev)
    elif ev.key == "ArrowLeft":
        this.prev_page(ev)


def receive_props(n_props):
    if n_props.location != this.props.location:
        this.get_item(go=utils.get_query("go"))
        scroll_top = this.props.scroll_top if utils.defined(this.props.scroll_top) else True
        if scroll_top:
            el = this.props.context or this.state.context or state.container_ref
            utils.scroll_to_element(el)


def page_render():
    number = 0
    p_id = this.state.id
    name = ""
    hash_id = ""
    path = ""
    fav = 0
    if this.state.data:
        p_id = this.state.data.id
        number = this.state.data.number
        name = this.state.data.name
        hash_id = this.state.data.hash
        path = this.state.data.path
        if this.state.data.metatags.favorite:
            fav = 1

    img = None
    __pragma__("iconv")
    if number in this.state.other:
        img = this.state.other[number].img
    __pragma__("noiconv")

    n_url = utils.build_url(query={'id': p_id, 'go': "next"})
    p_url = utils.build_url(query={'id': p_id, 'go': "prev"})

    rows = []

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Rating, icon="heart", size="massive", rating=fav),
                    colSpan="2", collapsing=True)))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, "Tags:", as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(tagview.TagView, item_id=p_id, item_type=this.state.item_type))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, "Path:", as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, path))))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, "Hash:", as_="h5"), collapsing=True),
                  e(ui.Table.Cell, e(ui.Label, hash_id))))

    return e(ui.Grid,
             e(PageNav, number=number, count=this.state.pages,
               n_url=n_url, p_url=p_url),
             e(ui.Grid.Row,
               e(ui.Ref,
                 e(ui.Grid.Column,
                   e(Link,
                     e(thumbitem.Thumbnail,
                       img=img,
                       item_id=p_id,
                       item_type=this.state.item_type,
                       size_type=ImageSize.Original,
                       centered=True,
                       fluid=False,
                       bordered=True,
                       placeholder="",
                       inverted=True,
                       ),
                     to=n_url,
                     ),
                   className="no-padding-segment"
                   ),
                 innerRef=this.set_context,
                 ),
               centered=True,
               textAlign="center",
               ),
             e(PageNav, number=number, count=this.state.pages,
               n_url=n_url, p_url=p_url),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Segment,
                   e(ui.Table,
                     e(ui.Table.Body,
                       *rows
                       ),
                     basic="very",
                     ),
                   as_=ui.Container,
                   ))),
             padded=True,
             inverted=True,
             )


Page = createReactClass({
    'displayName': 'Page',

    'getInitialState': lambda: {'id': int(utils.get_query("id", 0)),
                                'gid': int(utils.get_query("gid", 0)),
                                'other': {},
                                'pages': None,
                                'data': this.props.data,
                                'tag_data': this.props.tag_data or {},
                                'item_type': ItemType.Page,
                                'loading': True,
                                'context': None
                                },

    'cmd_data': None,
    'set_thumbs': set_thumbs,
    'get_thumbs': get_thumbs,
    'get_item': get_item,
    'get_other': get_other,
    'get_pages': get_pages,
    'on_key': on_key,
    'prev_page': lambda e: all((utils.go_to(this.props.history, query={'id': this.state.data.id, 'go': "prev"}),)),
    'next_page': lambda e: all((utils.go_to(this.props.history, query={'id': this.state.data.id, 'go': "next"}),)),
    'back_to_gallery': lambda: utils.go_to(this.props.history, "/item/gallery", query={'id': utils.get_query("gid") or this.state.data.gallery_id}, keep_query=False),

    'set_context': lambda c: this.setState({'context': c}),
    'componentWillReceiveProps': receive_props,
    'componentDidMount': lambda: window.addEventListener("keydown", this.on_key, False),
    'componentWillUnmount': lambda: window.removeEventListener("keydown", this.on_key, False),

    'componentWillMount': lambda: all((this.props.menu([
        e(ui.Menu.Menu, e(ui.Menu.Item, icon="arrow up", onClick=this.back_to_gallery)),
    ]),
        (this.get_item(go=utils.get_query("go")) if not this.state.data else None),
    )),

    'render': page_render
})
