from src.react_utils import (e,
                             createReactClass,
                             Link)
from src.ui import ui, TitleChange
from src.i18n import tr
from src.state import state
from src.client import (ItemType, ImageSize, client, Command)
from src.single import thumbitem, pageitem
from src.views import tagview, itemview
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
screen = Object = Date = None
__pragma__('noskip')


def pagenav_render():
    els = []
    props = this.props

    if props.number > 1:
        els.append(e(ui.Button, icon="long arrow alternate left", as_=Link, to=props.p_url))

    curr_page_txt = str(props.number) + "/" + str(props.count) if props.count else props.number

    els.append(e(ui.Popup,
                 e(ui.Form,
                   e(ui.Form.Field,
                     e(ui.Input,
                       onChange=this.on_page_input,
                       size="mini",
                       js_type="number",
                       placeholder=props.number,
                       action=e(ui.Button, js_type="submit", compact=True,
                                icon="share",
                                onClick=this.go_to_page),
                       min=1, max=str(props.count) if props.count else props.number),
                     ),
                   onSubmit=this.go_to_page
                   ),
                 on="click",
                 hoverable=True,
                 position="top center",
                 trigger=e(ui.Button, curr_page_txt, basic=True))
               )

    if props.number < props.count and props.n_url:
        els.append(e(ui.Button, icon="long arrow alternate right", as_=Link, to=props.n_url))

    return e(ui.Grid.Row,
             e(ui.Grid.Column,
               *els,
               textAlign="center",
               ),
             columns=1
             )


PageNav = createReactClass({
    'displayName': 'PageNav',

    'getInitialState': lambda: {
        'go_to_page': None,
    },

    'on_page_input': lambda e, d: this.setState({'go_to_page': d.value}),
    'go_to_page': lambda: utils.go_to(this.props.history, this.props.get_page_url(this.state.go_to_page)) if this.state.go_to_page and this.props.get_page_url else None,

    'render': pagenav_render,
}, pure=True)


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
                             size=this.state.image_size, url=True, uri=True,
                             item_type=this.state.item_type)


def get_pages(data=None, error=None, gid=None, limit=50):
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
                utils.go_to(this.props.history, this.get_page_url(1), query={"retry": True}, push=False)
    elif error:
        state.app.notif("Failed to fetch item ({})".format(this.state.id), level="error")
    else:
        gid = int(this.props.match.params.gallery_id)
        number = int(this.props.match.params.page_number)
        client.log("Fetching page: " + number)
        if this.state.data and number == this.state.data.number:
            client.log("Current page data is the same")
            return

        if this.state.pages:
            if number in this.state.pages:
                client.log("Retrieving cached page")
                this.setState({'data': this.state.pages[number]['data']})
                return
        client.log("Retrieving new page")
        if gid:
            client.call_func("get_page", this.get_item, gallery_id=gid, number=number, ctx=True)
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


def get_gallery(data=None, error=None):
    if data is not None and not error:
        this.setState({"gallery": data})
    elif error:
        state.app.notif("Failed to fetch gallery item ({})".format(this.state.id), level="error")
    else:
        if this.props.location.state and this.props.location.state.gallery:
            this.get_gallery(this.props.location.state.gallery)
            return
        gid = int(this.props.match.params.gallery_id)
        if gid:
            client.call_func("get_item", this.get_gallery, item_type=ItemType.Gallery, item_id=gid)


def get_page_url(number, gid=None):
    return "/item/gallery/{}/page/{}".format(
        this.props.match.params.gallery_id if gid is None else gid,
        number)


__pragma__("nokwargs")


def get_default_size():
    w = window.innerWidth
    s = screen.width
    if w > 2400 or s > 2400:
        return ImageSize.Original
    if w > 1600 or s > 1600:
        return ImageSize.x2400
    elif w > 1280 or s > 1600:
        return ImageSize.x1600
    elif w > 980:
        return ImageSize.x1280
    elif w > 768:
        return ImageSize.x960
    else:
        return ImageSize.x768


def go_next():
    if int(this.state.data.number) < int(this.state.page_count):
        utils.go_to(this.props.history, this.get_page_url(this.state.data.number + 1))


def go_prev():
    if int(this.state.data.number) > 1:
        utils.go_to(this.props.history, this.get_page_url(this.state.data.number - 1))


def go_left():
    if this.state.cfg_direction == ReaderDirection.left_to_right:
        this.go_prev()
    elif this.state.cfg_direction == ReaderDirection.right_to_left:
        this.go_next()


def go_right():
    if this.state.cfg_direction == ReaderDirection.left_to_right:
        this.go_next()
    elif this.state.cfg_direction == ReaderDirection.right_to_left:
        this.go_prev()


def on_key(ev):
    if ev.key == "Escape":
        ev.preventDefault()
        this.back_to_gallery()
    elif ev.key in ("ArrowRight", "d"):
        ev.preventDefault()
        this.go_right()
    elif ev.key in ("ArrowLeft", "a"):
        ev.preventDefault()
        this.go_left()


def update_metatags(mtags):
    if this.state.data:
        client.call_func("update_metatags", None, item_type=this.state.item_type,
                         item_id=this.state.data.id, metatags=mtags)
        d = this.state.data
        d.metatags = dict(d.metatags)
        d.metatags.update(mtags)
        d = utils.JSONCopy(d)
        this.setState({'data': d})


def on_canvas_click(ev):
    if this.state.context:
        ev.preventDefault()
        rect = this.state.context.getBoundingClientRect()
        x, y = ev.clientX - rect.left, ev.clientY - rect.top  # noqa: F841
        hwidth = rect.width / 2
        if x > hwidth:
            this.go_right()
        else:
            this.go_left()


def on_update(p_props, p_state):
    if p_state.data != this.state.data:
        this.setState({'number': this.state.data.number})

    if any((p_props.match.params.page_number != this.props.match.params.page_number,
            )):
        this.get_item()
        this.setState({'config_visible': False})
        if not this.state.cfg_pagelist_open:
            this.setState({'pages_visible': False})
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
    number = this.state.number
    p_id = 0
    hash_id = ""
    path = ""
    fav = 0
    all_pages = this.state.pages
    if this.state.data:
        p_id = this.state.data.id
        number = this.state.data.number
        hash_id = this.state.data.hash
        path = this.state.data.path
        if this.state.data.metatags.favorite:
            fav = 1

    page_title = "",
    if this.state.gallery:
        if this.state.gallery.preferred_title:
            t = this.state.gallery.preferred_title.js_name
            page_title = "{} {} | {}".format(tr(this, "ui.t-page", "Page"), number, t)

    img = None
    __pragma__("iconv")
    if number in this.state.pages:
        img = this.state.pages[number].img
    __pragma__("noiconv")

    n_url = ""
    if int(number) < int(this.state.page_count):
        n_url = this.get_page_url(int(number) + 1)
    p_url = this.get_page_url(int(number) - 1)

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
              size_type=this.state.image_size,
              centered=True,
              fluid=False,
              bordered=True,
              placeholder="",
              inverted=this.state.cfg_invert,
              style=thumb_style,
              className=thumb_class
              )

    rows = []

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Rating, icon="heart", size="massive", rating=fav, onRate=this.favorite),
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
        {'key': 1, 'text': tr(this, "ui.t-left-to-right", 'Left to Right'), 'value': ReaderDirection.left_to_right},
        {'key': 2, 'text': tr(this, "ui.t-rigt-to-left", 'Right to Left'), 'value': ReaderDirection.right_to_left},
    ]

    cfg_scaling = [
        {'key': 1, 'text': tr(this, "ui.t-default", 'Default'), 'value': ReaderScaling.default},
        {'key': 2, 'text': tr(this, "ui.t-fit-width", 'Fit Width'), 'value': ReaderScaling.fit_width},
        {'key': 3, 'text': tr(this, "ui.t-fit-height", 'Fit Height'), 'value': ReaderScaling.fit_height},
    ]

    cfg_size = [
        {'key': 1, 'text': tr(this, "ui.t-original", 'Original'), 'value': ImageSize.Original},
        {'key': 2, 'text': "x2400", 'value': ImageSize.x2400},
        {'key': 3, 'text': "x1600", 'value': ImageSize.x1600},
        {'key': 4, 'text': "x1280", 'value': ImageSize.x1280},
        {'key': 5, 'text': "x960", 'value': ImageSize.x960},
        {'key': 5, 'text': "x768", 'value': ImageSize.x768},
    ]

    return e(ui.Sidebar.Pushable,
             e(TitleChange, title=page_title),
             e(ui.Ref,
               e(ui.Sidebar,
                 e(itemview.SimpleView,
                   e(ui.Card.Group,
                     *[e(pageitem.Page,
                         data=all_pages[x]['data'],
                         centered=True,
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
                 e(ui.Form.Select, options=cfg_direction, label=tr(this, "ui.t-reading-direction", "Reading Direction"),
                   defaultValue=this.state.cfg_direction, onChange=this.set_cfg_direction),
                 e(ui.Form.Select, options=cfg_scaling, label=tr(this, "ui.t-scaling", "Scaling"),
                   defaultValue=this.state.cfg_scaling, onChange=this.set_cfg_scaling),
                 e(ui.Form.Select, options=cfg_size, label=tr(this, "ui.t-size", "Size"),
                   defaultValue=this.state.image_size, onChange=this.set_cfg_size),
                 e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "ui.t-stretch-pages", "Stretch small pages"), toggle=True,
                   defaultChecked=this.state.cfg_strecth, onChange=this.set_cfg_stretch),
                 e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "ui.t-invert-bg-color", "Invert background color"), toggle=True,
                   defaultChecked=this.state.cfg_invert, onChange=this.set_cfg_invert),
                 e(ui.Form.Field, control=ui.Checkbox, label=tr(this, "ui.t-keep-pagelist-open", "Keep pagelist open"), toggle=True,
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
                   n_url=n_url, p_url=p_url,
                   get_page_url=this.get_page_url,
                   history=this.props.history),
                 e(ui.Grid.Row,
                   e(ui.Ref,
                     e(ui.Grid.Column,
                       e(ui.Segment,
                         thumb,
                         className="no-padding-segment force-viewport-size",
                         basic=True,
                         inverted=this.state.cfg_invert,
                         ),
                       className="no-padding-segment",
                       onClick=this.on_canvas_click,
                       style={'cursor': 'pointer'},
                       ),
                     innerRef=this.set_context,
                     ),
                   centered=True,
                   textAlign="center",
                   ),
                 e(PageNav, number=number, count=this.state.page_count,
                   n_url=n_url, p_url=p_url,
                   get_page_url=this.get_page_url,
                   history=this.props.history),
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

    'get_page_url': get_page_url,

    'get_default_size': get_default_size,

    'getInitialState': lambda: {'gid': int(this.props.match.params.gallery_id),
                                'number': int(this.props.match.params.page_number),
                                'gallery': None,
                                'pages': {},
                                'page_list_ref': None,
                                'page_list_page': 0,
                                'page_list_loading': False,
                                'page_count': 0,
                                'data': this.props.data or {},
                                'tag_data': this.props.tag_data or {},
                                'item_type': ItemType.Page,
                                'image_size': utils.storage.get("reader_size", this.get_default_size()),
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
    'go_prev': go_prev,
    'go_next': go_next,
    'go_left': go_left,
    'go_right': go_right,
    'set_pagelist_ref': lambda r: this.setState({'page_list_ref': r}),
    'favorite': lambda e, d: all((this.update_metatags({'favorite': bool(d.rating)}),
                                  e.preventDefault())),
    'update_metatags': update_metatags,
    'set_thumbs': set_thumbs,
    'get_thumbs': get_thumbs,
    'get_item': get_item,
    'get_gallery': get_gallery,
    'get_pages': get_pages,
    'get_page_count': get_page_count,
    'on_key': on_key,
    'on_pagelist_load_more': lambda: this.get_pages(),
    'back_to_gallery': lambda: utils.go_to(this.props.history, "/item/gallery/{}".format(this.props.match.params.gallery_id), keep_query=False),

    'set_cfg_direction': lambda e, d: all((this.setState({'cfg_direction': d.value}), utils.storage.set("reader_direction", d.value))),
    'set_cfg_size': lambda e, d: all((this.setState({'image_size': d.value}), utils.storage.set("reader_size", d.value))),
    'set_cfg_scaling': lambda e, d: all((this.setState({'cfg_scaling': d.value}), utils.storage.set("reader_scaling", d.value))),
    'set_cfg_stretch': lambda e, d: all((this.setState({'cfg_stretch': d.checked}), utils.storage.set("reader_stretch", d.checked))),
    'set_cfg_invert': lambda e, d: all((this.setState({'cfg_invert': d.checked}), utils.storage.set("reader_invert", d.checked))),
    'set_cfg_pagelist_open': lambda e, d: all((this.setState({'cfg_pagelist_open': d.checked}), utils.storage.set("reader_pagelist_open", d.checked))),

    'toggle_config': lambda: this.setState({'config_visible': not this.state.config_visible, 'pages_visible': False}),
    'toggle_pages': lambda: this.setState({'pages_visible': not this.state.pages_visible, 'config_visible': False}),
    'set_context': lambda c: this.setState({'context': c}),
    'on_canvas_click': on_canvas_click,

    'componentDidUpdate': on_update,
    'componentDidMount': lambda: all((window.addEventListener("keydown", this.on_key, False), this.get_gallery())),
    'componentWillUnmount': lambda: all((window.removeEventListener("keydown", this.on_key, False),
                                         state.update({'reset_scroll': True})
                                         )),

    'componentWillMount': lambda: all((this.props.menu([
        e(ui.Menu.Item, e(ui.Icon, js_name="ellipsis vertical", size="large"),
          icon=True, onClick=this.toggle_pages, position="left"),
        e(ui.Menu.Menu, e(ui.Menu.Item, e(ui.Icon, js_name="level up alternate", size="large"), icon=True, as_=Link, to={'pathname': "/item/gallery/{}".format(this.props.match.params.gallery_id),
                                                                                                                         'state': {'gallery': this.state.gallery}})),
        e(ui.Menu.Item, e(ui.Icon, js_name="options", size="large"),
          icon=True, onClick=this.toggle_config, position="right"),
    ]),
        (this.get_item() if not this.state.data else None),
        state.update({'reset_scroll': False})
    )),

    'render': page_render
}, pure=True)
__pragma__("notconv")
__pragma__("nojsiter")
