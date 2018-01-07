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
        if this.state.cfg_direction == ReaderDirection.left_to_right:
            this.next_page(ev)
        elif this.state.cfg_direction == ReaderDirection.right_to_left:
            this.prev_page(ev)
    elif ev.key == "ArrowLeft":
        if this.state.cfg_direction == ReaderDirection.left_to_right:
            this.prev_page(ev)
        elif this.state.cfg_direction == ReaderDirection.right_to_left:
            this.next_page(ev)


def receive_props(n_props):
    if n_props.location != this.props.location:
        this.get_item(go=utils.get_query("go"))
        scroll_top = this.props.scroll_top if utils.defined(this.props.scroll_top) else True
        if scroll_top:
            el = this.props.context or this.state.context or state.container_ref
            utils.scroll_to_element(el)


class ReaderDirection:
    left_to_right = 1
    right_to_left = 2


class ReaderScaling:
    default = 1
    fit_width = 2
    fit_height = 3


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

    # config

    cfg_direction = [
        {'key': 1, 'text': tr(this, "", 'Left to Right'), 'value': ReaderDirection.left_to_right},
        {'key': 2, 'text': tr(this, "", 'Right to Left'), 'value': ReaderDirection.right_to_left},
    ]

    cfg_scaling = [
        {'key': 1, 'text': tr(this, "", 'Default'), 'value': ReaderScaling.default},
        {'key': 2, 'text': tr(this, "", 'Fit Width'), 'value': ReaderScaling.fit_width},
        {'key': 3, 'text': tr(this, "", 'Fit Height'), 'value': ReaderScaling.fit_height},
    ]

    thumb_style = {}
    thumb_class = ''
    if this.state.cfg_stretch:
        if this.state.cfg_scaling == ReaderScaling.fit_width:
            thumb_class = 'reader-fitwidth-stretch'
        elif this.state.cfg_scaling == ReaderScaling.fit_height:
            thumb_class = 'reader-fitheight-stretch'
    else:
        if this.state.cfg_scaling == ReaderScaling.fit_width:
            thumb_class = 'reader-fitwidth'
        elif this.state.cfg_scaling == ReaderScaling.fit_height:
            thumb_class = 'reader-fitheight'

    return e(ui.Sidebar.Pushable,
             e(ui.Sidebar,  # wait for infinite scroll, then a page list can be implemented here
               as_=ui.Segment,
                 size="small",
                 basic=True,
                 visible=this.state.pages_visible and not this.state.config_visible,
                 direction="left",
                 animation="slide along",
                 loading=this.state.pages_loading,
               ),
             e(ui.Sidebar,
               e(ui.Form,
                 e(ui.Form.Select, options=cfg_direction, label=tr(this, "", "Reading Direction"),
                   defaultValue=this.state.cfg_direction, onChange=this.set_cfg_direction),
                 e(ui.Form.Select, options=cfg_scaling, label=tr(this, "", "Scaling"),
                   defaultValue=this.state.cfg_scaling, onChange=this.set_cfg_scaling),
                 e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "", "Stretch small pages"), toggle=True,
                   defaultChecked=this.state.cfg_strecth, onChange=this.set_cfg_stretch),
                 e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "", "Invert background color"), toggle=True,
                   defaultChecked=this.state.cfg_invert, onChange=this.set_cfg_invert),
                 e(ui.Form.Field, "Close", control=ui.Button),
                 onSubmit=this.toggle_config,
                 ),
               as_=ui.Segment,
                 size="small",
                 basic=True,
                 visible=this.state.config_visible and not this.state.pages_visible,
                 direction="right",
                 animation="slide along",
               ),
             e(ui.Sidebar.Pusher,
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
                           inverted=this.state.cfg_invert,
                           style=thumb_style,
                           className=thumb_class
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
                 inverted=this.state.cfg_invert,
                 as_=ui.Grid,
               )
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
                                'context': None,
                                'config_visible': False,
                                'pages_visible': False,
                                'cfg_direction': utils.storage.get("reader_direction", ReaderDirection.left_to_right),
                                'cfg_scaling': utils.storage.get("reader_scaling", ReaderScaling.default),
                                'cfg_stretch': utils.storage.get("reader_stretch", False),
                                'cfg_invert': utils.storage.get("reader_invert", True),
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

    'set_cfg_direction': lambda e, d: all((this.setState({'cfg_direction': d.value}), utils.storage.set("reader_direction", d.value))),
    'set_cfg_scaling': lambda e, d: all((this.setState({'cfg_scaling': d.value}), utils.storage.set("reader_scaling", d.value))),
    'set_cfg_stretch': lambda e, d: all((this.setState({'cfg_stretch': d.checked}), utils.storage.set("reader_stretch", d.checked))),
    'set_cfg_invert': lambda e, d: all((this.setState({'cfg_invert': d.checked}), utils.storage.set("reader_invert", d.checked))),

    'toggle_config': lambda: this.setState({'config_visible': not this.state.config_visible, 'pages_visible': False}),
    'toggle_pages': lambda: this.setState({'pages_visible': not this.state.pages_visible, 'config_visible': False}),
    'set_context': lambda c: this.setState({'context': c}),
    'componentWillReceiveProps': receive_props,
    'componentDidMount': lambda: window.addEventListener("keydown", this.on_key, False),
    'componentWillUnmount': lambda: window.removeEventListener("keydown", this.on_key, False),

    'componentWillMount': lambda: all((this.props.menu([
        #e(ui.Menu.Item, e(ui.Icon, js_name="sidebar", size="large"), icon=True, onClick=this.toggle_pages, position="left"),
        e(ui.Menu.Menu, e(ui.Menu.Item, e(ui.Icon, js_name="arrow up", size="large"), icon=True, onClick=this.back_to_gallery)),
        e(ui.Menu.Item, e(ui.Icon, js_name="options", size="large"),
          icon=True, onClick=this.toggle_config, position="right"),
    ]),
        (this.get_item(go=utils.get_query("go")) if not this.state.data else None),
    )),

    'render': page_render
})
