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
from src.single import thumbitem, pageitem
from src.views import tagview, itemview
from src import utils


def PageNav(props):
    els = []
    if props.number > 1:
        els.append(e(ui.Button, icon="arrow left", as_=Link, to=props.p_url))
    els.append(e(ui.Button, str(props.number) + "/" + str(props.count) if props.count else props.number))
    if props.number < props.count and props.n_url:
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
__pragma__("jsiter")


def set_thumbs(cmd):
    if this.cmd_data and this.state.pages:
        values = cmd.get_value()
        d = this.state.pages
        for pnumb in d:
            if not d[pnumb].img:
                p = d[pnumb]['data']
                d[pnumb]['img'] = values[this.cmd_data[p.id]]['data']
        this.setState({'pages': d})


__pragma__("nojsiter")


__pragma__("kwargs")


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


def get_pages(data=None, error=None, gid=None):
    if data is not None and not error:
        pages = this.state.pages
        for p in data:
            pages[p.number] = {}
            pages[p.number]['data'] = p
        this.setState({'pages': pages, 'page_list_loading': False})
        this.get_thumbs(other=data)
    else:
        if this.state.data:
            gid = this.state.data.gallery_id
        page = this.state.page_list_page
        this.setState({'page_list_loading': True, "page_list_page": page + 1})
        limit = 50
        client.call_func("get_related_items",
                         this.get_pages, item_type=ItemType.Gallery,
                         item_id=gid, limit=limit, offset=page * limit)


__pragma__("nokwargs")


def get_item(ctx=None, data=None, error=None):
    if ctx is not None and not error:
        if data is not None:
            this.setState({"data": data, "loading": False})
            if not this.state.pages:
                this.get_page_count(gid=data.gallery_id)
                this.get_pages(gid=data.gallery_id)
        else:
            if not utils.get_query("retry"):
                utils.go_to(this.props.history, query={"number": 1, "retry": True}, push=False)
    elif error:
        state.app.notif("Failed to fetch item ({})".format(this.state.id), level="error")
    else:
        item = this.state.item_type
        gid = utils.get_query("gid")
        pid = utils.get_query("id")

        if this.state.data and utils.get_query("number") == this.state.data.number:
            return

        number = utils.get_query("number", 1)

        if this.state.pages:
            if number in this.state.pages:
                this.setState({'data': this.state.pages[number]['data']})
                return
        if gid:
            client.call_func("get_page", this.get_item, gallery_id=gid, number=number, ctx=True)
            this.setState({'loading': True})
        elif pid:
            client.call_func("get_page", this.get_item, page_id=pid, number=number, ctx=True)
            this.setState({'loading': True})


__pragma__("noiconv")
__pragma__("notconv")

__pragma__("kwargs")


def get_page_count(data=None, error=None, gid=None):
    if data is not None and not error:
        this.setState({"page_count": data['count']})
    elif error:
        state.app.notif("Failed to fetch pages ({})".format(this.state.gid), level="error")
    else:
        item = ItemType.Gallery
        item_id = gid
        if item and item_id:
            client.call_func("get_related_count", this.get_page_count, item_type=item, item_id=item_id,
                             related_type=this.state.item_type)


__pragma__("nokwargs")


def on_key(ev):
    if ev.preventDefaulted:
        return

    history = this.props.history
    gallery_id = this.state.data.gallery_id
    number = this.state.data.number
    page_count = this.state.page_count

    def go_prev(): return utils.go_to(
        history,
        query={
            'gid': gallery_id,
            "number": number - 1})

    def go_next():
        if int(number) < int(page_count):
            return utils.go_to(
                history,
                query={
                    'gid': gallery_id,
                    "number": number + 1})

    def go_last(): return utils.go_to(
        history,
        query={
            'gid': gallery_id,
            "number": number - 1})

    if ev.key == "Escape":
        this.back_to_gallery()
    elif ev.key in ("ArrowRight", "d"):
        if this.state.cfg_direction == ReaderDirection.left_to_right:
            go_next()
        elif this.state.cfg_direction == ReaderDirection.right_to_left:
            go_prev()
    elif ev.key in ("ArrowLeft", "a"):
        if this.state.cfg_direction == ReaderDirection.left_to_right:
            go_prev()
        elif this.state.cfg_direction == ReaderDirection.right_to_left:
            go_next()


def on_update(p_props, p_state):
    if p_state.data != this.state.data:
        query = {
            'gid': this.state.data.gallery_id,
            "number": this.state.data.number}
        this.setState({'config_visible': False})
        if not this.state.cfg_pagelist_open:
            this.setState({'pages_visible': False})
        utils.go_to(this.props.history, query=query, push=False)


def receive_props(n_props):
    if n_props.location != this.props.location:
        this.get_item()
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


__pragma__("tconv")
__pragma__("jsiter")


def page_render():
    number = 0
    p_id = this.state.id
    name = ""
    hash_id = ""
    path = ""
    fav = 0
    gid = this.state.gid
    all_pages = this.state.pages
    if this.state.data:
        gid = this.state.data.gallery_id
        p_id = this.state.data.id
        number = this.state.data.number
        name = this.state.data.name
        hash_id = this.state.data.hash
        path = this.state.data.path
        if this.state.data.metatags.favorite:
            fav = 1

    img = None
    __pragma__("iconv")
    if number in this.state.pages:
        img = this.state.pages[number].img
    __pragma__("noiconv")

    n_url = ""
    if int(number) < int(this.state.page_count):
        n_url = utils.build_url(query={'gid': gid, "number": int(number) + 1})
    p_url = utils.build_url(query={'gid': gid, "number": int(number) - 1})

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

    thumb = e(thumbitem.Thumbnail,
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
              )
    if n_url:
        thumb = e(Link, thumb, to=n_url)

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

    set_page = this.set_page
    return e(ui.Sidebar.Pushable,
             e(ui.Ref,
               e(ui.Sidebar,
                 e(itemview.SimpleView,
                   e(ui.Card.Group,
                     *[e(pageitem.Page,
                         data=all_pages[x]['data'],
                         centered=True,
                         link=False,
                         onClick=set_page,
                         ) for x in all_pages],
                     itemsPerRow=2,
                     ),
                   on_load_more=this.on_pagelist_load_more,
                   loading=this.state.page_list_loading,
                   context=this.state.page_list_ref,
                   ),
                 as_=ui.Segment,
                 size="small",
                 visible=this.state.pages_visible,
                 direction="left",
                 animation="overlay",
                 loading=this.state.pages_loading,
                 ),
               innerRef=this.set_pagelist_ref,
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
                 e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "", "Keep pagelist open"), toggle=True,
                   defaultChecked=this.state.cfg_pagelist_open, onChange=this.set_cfg_pagelist_open),
                 e(ui.Form.Field, "Close", control=ui.Button),
                 onSubmit=this.toggle_config,
                 ),
               as_=ui.Segment,
                 size="small",
                 visible=this.state.config_visible,
                 direction="right",
                 animation="overlay",
               ),
             e(ui.Sidebar.Pusher,
                 e(PageNav, number=number, count=this.state.page_count,
                   n_url=n_url, p_url=p_url),
                 e(ui.Grid.Row,
                   e(ui.Ref,
                     e(ui.Grid.Column,
                       thumb,
                       className="no-padding-segment"
                       ),
                     innerRef=this.set_context,
                     ),
                   centered=True,
                   textAlign="center",
                   ),
                 e(PageNav, number=number, count=this.state.page_count,
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
                                'pages': {},
                                'page_list_ref': None,
                                'page_list_page': 0,
                                'page_list_loading': False,
                                'page_count': 0,
                                'data': this.props.data or {},
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
                                'cfg_pagelist_open': utils.storage.get("reader_pagelist_open", False),
                                },

    'cmd_data': None,
    'set_page': lambda e, d: this.setState({'data': d}),
    'set_pagelist_ref': lambda r: this.setState({'page_list_ref': r}),
    'set_thumbs': set_thumbs,
    'get_thumbs': get_thumbs,
    'get_item': get_item,
    'get_pages': get_pages,
    'get_page_count': get_page_count,
    'on_key': on_key,
    'on_pagelist_load_more': lambda: this.get_pages(),
    'back_to_gallery': lambda: utils.go_to(this.props.history, "/item/gallery", query={'id': utils.get_query("gid") or this.state.data.gallery_id}, keep_query=False),

    'set_cfg_direction': lambda e, d: all((this.setState({'cfg_direction': d.value}), utils.storage.set("reader_direction", d.value))),
    'set_cfg_scaling': lambda e, d: all((this.setState({'cfg_scaling': d.value}), utils.storage.set("reader_scaling", d.value))),
    'set_cfg_stretch': lambda e, d: all((this.setState({'cfg_stretch': d.checked}), utils.storage.set("reader_stretch", d.checked))),
    'set_cfg_invert': lambda e, d: all((this.setState({'cfg_invert': d.checked}), utils.storage.set("reader_invert", d.checked))),
    'set_cfg_pagelist_open': lambda e, d: all((this.setState({'cfg_pagelist_open': d.checked}), utils.storage.set("reader_pagelist_open", d.checked))),

    'toggle_config': lambda: this.setState({'config_visible': not this.state.config_visible, 'pages_visible': False}),
    'toggle_pages': lambda: this.setState({'pages_visible': not this.state.pages_visible, 'config_visible': False}),
    'set_context': lambda c: this.setState({'context': c}),
    'componentDidUpdate': on_update,
    'componentWillReceiveProps': receive_props,
    'componentDidMount': lambda: window.addEventListener("keydown", this.on_key, False),
    'componentWillUnmount': lambda: window.removeEventListener("keydown", this.on_key, False),

    'componentWillMount': lambda: all((this.props.menu([
        e(ui.Menu.Item, e(ui.Icon, js_name="list layout", size="large"),
          icon=True, onClick=this.toggle_pages, position="left"),
        e(ui.Menu.Menu, e(ui.Menu.Item, e(ui.Icon, js_name="arrow up", size="large"), icon=True, onClick=this.back_to_gallery)),
        e(ui.Menu.Item, e(ui.Icon, js_name="options", size="large"),
          icon=True, onClick=this.toggle_config, position="right"),
    ]),
        (this.get_item() if not this.state.data else None),
    )),

    'render': page_render
})
__pragma__("notconv")
__pragma__("nojsiter")
