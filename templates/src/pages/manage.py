from src.react_utils import (e,
                             h,
                             Route,
                             Redirect,
                             NavLink,
                             Link,
                             Switch,
                             Prompt,
                             createReactClass)
from src.ui import ui, Pagination, TitleChange
from src.client import (client, ItemType, Command,
                        TemporaryViewType, CommandState)
from src.single import artistitem, circleitem
from src.propsviews import gallerypropsview
from src.i18n import tr
from src.state import state
from src import utils
from org.transcrypt.stubs.browser import __pragma__

__pragma__('alias', 'as_', 'as')
__pragma__('alias', 'js_input', 'input')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Date = None
__pragma__('noskip')

__pragma__("kwargs")


def get_config(data=None, error=None, cfg={}):
    if data is not None and not error:
        this.setState({"config": data})
    elif error:
        state.app.notif("Failed to retrieve configuration", level="warning")
    else:
        client.call_func("get_config", this.get_config, cfg=cfg)


def set_config(data=None, error=None, cfg={}, save=True):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to update setting", level="warning")
    else:
        client.call_func("set_config", this.set_config, cfg=cfg)
        if save:
            client.call_func("save_config")


__pragma__("nokwargs")


def update_options(key, value):
    d = utils.JSONCopy(this.state.options)
    d[key] = value
    this.setState({'options': d})


def scan_galleries(data=None, error=None):
    if data is not None and not error:
        utils.session_storage.set("scan_view_id", data['view_id'])
        this.setState({'view_id': data['view_id']})
        this.scan_cmd = Command(data['command_id'], daemon=False)
        this.scan_cmd.poll_progress(interval=200, callback=this.on_scan_progress)
    elif error:
        state.app.notif("Failed to scan for galleries", level="error")
    else:
        this.setState({'view_progress_data': None})
        if this.state.path:
            utils.session_storage.set("scan_view_id", None)
            client.call_func("scan_galleries", this.scan_galleries, path=this.state.path)
            this.setState({'submitted_path': this.state.path,
                           'loading': True,
                           'view_id': None})


def on_scan_submit():
    this.scan_galleries()


def on_view_submit():
    this.submit_view()


def on_scan_progress(cmd):
    p = cmd.get_progress()
    this.setState({'progress_data': p})
    if p and p.state == CommandState.finished:
        this.setState({'loading': False})
        this.get_view()


def on_view_progress(cmd):
    p = cmd.get_progress()
    this.setState({'view_progress_data': p})
    if p and p.state == CommandState.finished:
        utils.session_storage.set("scan_view_id", None)
        this.setState({'view_loading': False, 'view_id': None})


def get_view(data=None, error=None):
    if data is not None and not error:
        this.setState({'view_data': data,
                       'view_loading': False})
    elif error:
        state.app.notif("Failed to fetch temporary view", level="error")
    else:
        if this.state.view_id:
            this.setState({'view_loading': True})
            client.call_func("temporary_view", this.get_view,
                             view_type=TemporaryViewType.GalleryAddition,
                             view_id=this.state.view_id,
                             limit=this.state.limit,
                             offset=this.state.limit * (this.state.page - 1))


def submit_view(data=None, error=None):
    if data is not None and not error:
        this.view_cmd = Command(data, daemon=False)
        this.view_cmd.poll_progress(interval=200, callback=this.on_view_progress)
    elif error:
        state.app.notif("Failed to submit temporary view", level="error")
    else:
        if this.state.view_id:
            this.setState({'view_loading': True, 'view_data': {}})
            client.call_func("submit_temporary_view", this.submit_view,
                             view_type=TemporaryViewType.GalleryAddition,
                             view_id=this.state.view_id,
                             )


def scanpage_update(p_p, p_s):
    if any((
        p_s.page != this.state.page,
    )):
        this.get_view()


__pragma__("tconv")


def scanpage_render():

    view_data = this.state.view_data
    progress_text = ""
    title = ""
    percent = 0
    if this.state.progress_data:
        p = this.state.progress_data
        progress_text = p.text
        title = p.title
        percent = p.percent

    pages_el = []
    count_el = []
    if not this.state.loading and view_data:
        if view_data['count'] > this.state.limit:
            pages_el.append(
                e(ui.Grid.Row,
                    e(ui.Responsive,
                        e(Pagination,
                            limit=1,
                            pages=view_data['count'] / this.state.limit,
                            current_page=this.state.page,
                            on_change=this.set_page,
                            query=True,
                            scroll_top=True,
                            size="tiny"),
                        maxWidth=578,
                      ),
                    e(ui.Responsive,
                        e(Pagination,
                            pages=view_data['count'] / this.state.limit,
                            current_page=this.state.page,
                            on_change=this.set_page,
                            query=True,
                            scroll_top=True),
                        minWidth=579,
                      ),
                    centered=True
                  ),
            )
            count_el.append(e(ui.Grid.Row,
                              e(ui.Grid.Column,
                                e(ui.Header,
                                  e(ui.Header.Subheader,
                                    tr(this,
                                       "ui.t-showing-count",
                                       "Showing {}".format(view_data['count']),
                                       placeholder={
                                           'from': (
                                               this.state.page -
                                               1) *
                                           this.state.limit +
                                           1,
                                           'to': (
                                               this.state.page -
                                               1) *
                                           this.state.limit +
                                           len(view_data['items']),
                                           'all': view_data['count']}
                                       ),
                                      as_="h6"),
                                  ),
                                  textAlign="center", width=16)))

    items = []
    view_progress_data = this.state.view_progress_data

    view_progress_el = []
    submitted_view_data = view_progress_data
    if submitted_view_data:
        p_kwargs = {}
        p_kwargs['progress'] = 'value'
        if view_progress_data['max']:
            p_kwargs['value'] = view_progress_data['value']
            p_kwargs['total'] = view_progress_data['max']
            p_kwargs['autoSuccess'] = True
        else:
            p_kwargs['percent'] = 1
            p_kwargs['autoSuccess'] = False
        view_progress_el.append(e(ui.Segment,
                                  e(ui.Progress,
                                    precision=2,
                                    indicating=True,
                                    active=True,
                                    **p_kwargs),
                                  basic=True
                                  ))

    if not this.state.loading and view_data:
        for t in this.state.view_data['items']:
            all_circles = []
            [all_circles.extend(a.circles) for a in t.gallery.artists]
            circles = []
            circle_names = []
            for c in all_circles:
                if c.js_name not in circle_names:
                    circles.append(c)
                    circle_names.append(c.js_name)

            items.append(
                e(ui.List.Item,
                  e(ui.List.Content,
                    *(e(ui.Header, x, className="sub-text", as_="h5") for x in t.sources),
                    e(ui.List.Description,
                      e(ui.List, [e(ui.List.Item, e(ui.Header, x.js_name, size="tiny"),) for x in t.gallery.titles],
                        size="tiny", relaxed=True, bulleted=True),
                      e(ui.Divider, hidden=True),
                      e(ui.List,
                        e(ui.List.Item, h("span", tr(this, "ui.t-artist", "Artist") + ':', size="tiny",
                                          className="sub-text"), *(e(artistitem.ArtistLabel, data=x) for x in t.gallery.artists)),
                        e(ui.List.Item, h("span", tr(this, "ui.t-circle", "Circle") +
                                          ':', size="tiny", className="sub-text"), *
                          ((e(circleitem.CircleLabel, data=x) for x in circles)) if circles else []),
                          e(ui.List.Item, h("span", tr(this, "general.db-item-collection", "Collection") + ':',
                                            size="tiny", className="sub-text"), *(e(ui.Label, x.js_name) for x in t.gallery.collections)),
                        e(ui.List.Item, h("span", tr(this, "ui.t-language", "Language") +
                                          ':', size="tiny", className="sub-text"), *
                          ([e(ui.Label, t.gallery.language.js_name)] if t.gallery.language else [])),
                        e(ui.List.Item, h("span", tr(this, "ui.t-pages", "Pages") +
                                          ': ', size="tiny", className="sub-text"), t.page_count),
                        horizontal=True, relaxed=True, divided=True,
                        ),
                        *((e(ui.Label,
                             e(ui.Icon, js_name="checkmark"),
                             tr(this, "ui.t-metadata-file", "Metadata file"),
                             title=tr(this, "ui.t-metadata-from-file", "Metadata was retrieved from file"),
                             color="green", basic=True,
                             className="right", size="small"),) if t.metadata_from_file else []),
                      e(ui.Divider, hidden=True, clearing=True),
                      )
                    ),
                  ),
            )
    options_el = e(ui.Segment,
                   e(ui.Form,
                     e(ui.Form.Group,
                       e(ui.Form.Checkbox,
                         toggle=True,
                         label=tr(this, "ui.t-add-to-inbox", "Add to inbox"),
                         checked=this.state['gallery.add_to_inbox'] if utils.defined(
                             this.state['gallery.add_to_inbox']) else this.state.config['gallery.add_to_inbox'] if utils.defined(
                             this.state.config['gallery.add_to_inbox']) else False,
                           onChange=this.on_add_to_inbox,
                         ),
                         e(ui.Form.Checkbox,
                           toggle=True,
                           label=tr(this, "ui.t-scan-for-new-galleries", "Only show new"),
                           checked=not (
                               this.state['scan.skip_existing_galleries'] if utils.defined(
                                   this.state['scan.skip_existing_galleries']) else not this.state.config['scan.skip_existing_galleries'] if utils.defined(
                                   this.state.config['scan.skip_existing_galleries']) else False),
                           onChange=this.on_only_new,
                           ),
                         inline=True,
                       ),
                     ),
                   secondary=True)

    return h("div",
             e(TitleChange, title=tr(this, "ui.mi-scan", "Scan")),
             e(ui.Container,
                 e(ui.Message, e("div", dangerouslySetInnerHTML={
                   '__html': utils.marked(tr(this, "ui.de-scan-info", ""))}),
                   ),
                 e(ui.Divider, hidden=True),
                 e(ui.Form,
                     e(ui.Form.Group,
                       e(ui.Form.Input,
                         width=16,
                         fluid=True,
                         action=tr(this, "ui.mi-scan", "Scan"),
                         placeholder=tr(this, "", "Directory"),
                         onChange=this.set_path,
                         ),
                       ),
                     onSubmit=this.on_scan_submit,
                   ),
                 options_el,
                 e(ui.Form,
                     *([e(ui.Divider, e(ui.Button, tr(this, "ui.t-submit", "Submit"), disabled=submitted_view_data,
                                        primary=True, js_type="submit"), horizontal=True)] if view_data and view_data['items'] else []),
                     *view_progress_el,
                     e(ui.Grid,
                       *([e(ui.Label, title, attached="top")] if title else []),
                       e(ui.Dimmer,
                         e(ui.Loader,
                           e(ui.Statistic,
                             e(ui.Statistic.Value, "{}%".format(int(percent))),
                             e(ui.Statistic.Label, progress_text),
                             inverted=True,
                             size="mini"
                             ),
                           ),
                         active=this.state.loading,
                         ),
                       e(ui.Divider, hidden=True),
                       *count_el,
                       *pages_el,
                       e(ui.Grid.Row,
                         e(ui.Grid.Column,
                           e(ui.List, *items,
                             relaxed=True,
                             divided=True,
                             animated=True),
                           ),
                         ),
                       *pages_el,
                       *count_el,
                       as_=ui.Segment,
                       loading=this.state.view_loading,
                       secondary=True,
                       className="min-300-h",
                       ),
                     *([e(ui.Divider, e(ui.Button, tr(this, "ui.t-submit", "Submit"), disabled=submitted_view_data,
                                        primary=True, js_type="submit"), horizontal=True)] if view_data and view_data['items'] else []),
                     onSubmit=this.on_view_submit,
                   ),
               ))


__pragma__("notconv")


ScanPage = createReactClass({
    'displayName': 'ScanPage',

    'scan_cmd': None,

    'view_cmd': None,

    'getInitialState': lambda: {
        'config': {},
        'limit': 50,
        'page': utils.get_query("page", 1),
        'loading': False,
        'view_loading': False,
        'progress_data': None,
        'view_progress_data': None,
        'view_id': utils.session_storage.get("scan_view_id", None),
        'view_data': {},
        'path': "",
        'submitted_path': '',
        'gallery.add_to_inbox': js_undefined,
        'scan.skip_existing_galleries': js_undefined,
    },

    'set_path': lambda e, d: all((this.setState({'path': d.value}), )),

    'get_view': get_view,

    'submit_view': submit_view,

    'set_page': lambda p: all((this.setState({'page': p}), )),

    'scan_galleries': scan_galleries,

    'on_scan_submit': on_scan_submit,
    'on_view_submit': on_view_submit,

    'on_scan_progress': on_scan_progress,
    'on_view_progress': on_view_progress,

    'on_add_to_inbox': lambda e, d: all((this.setState({'gallery.add_to_inbox': d.checked}), this.set_config(cfg={'gallery.add_to_inbox': d.checked}, save=False), )),
    'on_only_new': lambda e, d: all((this.setState({'scan.skip_existing_galleries': not d.checked}), this.set_config(cfg={'scan.skip_existing_galleries': d.checked}, save=False), )),

    'get_config': get_config,
    'set_config': set_config,

    'componentDidUpdate': scanpage_update,

    'componentDidMount': lambda: all((this.get_view(), this.get_config(cfg={'gallery.add_to_inbox': True,
                                                                            'scan.skip_existing_galleries': True,
                                                                            }),
                                      )),

    'render': scanpage_render
})


def submit_gallery(data=None, error=None):
    if data is not None and not error:
        this.submit_txt = tr(this, "ui.t-new-gallery-added", "A new gallery was added"),
        Command(data, daemon=False).poll_progress(
            interval=200,
            callback=this.on_submitted)
    elif error:
        state.app.notif("Failed to submit new gallery", level="error")
        this.setState({'submitting': False})
    else:
        if this.state.new_data:
            this.state.new_data['pages'] = this.state.pages
            this.setState({'submitting': True})
            client.call_func("new_item", this.submit_gallery,
                             item_type=ItemType.Gallery,
                             item=this.state.new_data,
                             options=this.state.options,
                             )


def load_gallery(data=None, error=None):
    if data is not None and not error:
        this.setState({'data': data,
                       'pages': data.gallery.pages or [],
                       'new_data': data.gallery or {},
                       'gallery_data': data.gallery or {},
                       'load_gallery_loading': False,
                       'submitting': False})

    elif error:
        state.app.notif("Failed to load gallery", level="error")
        this.setState({'load_gallery_loading': False, 'submitting': False})
    else:
        this.setState({'load_gallery_loading': True})
        if this.state.load_gallery_path:
            client.call_func("load_gallery_from_path", this.load_gallery,
                             path=this.state.load_gallery_path)


__pragma__("kwargs")


def creategallery_on_update_data(*args, **kwargs):
    kwargs['data_state_key'] = 'gallery_data'
    this.update_data(*args, **kwargs)


__pragma__("nokwargs")


def creategallery_update(p_p, p_s):
    if p_s.gallery_data != this.state.gallery_data:
        data = this.state.data or {}
        data['gallery'] = this.state.gallery_data
        this.setState({'data': utils.JSONCopy(data)})


def creategallery_render():
    gallery_data = this.state.gallery_data

    options_el = e(ui.Segment,
                   e(ui.Form,
                     e(ui.Form.Group,
                       e(ui.Form.Checkbox,
                         toggle=True,
                         label=tr(this, "ui.t-add-to-inbox", "Add to inbox"),
                         checked=this.state.options['gallery.add_to_inbox'],
                         onChange=this.on_add_to_inbox,
                         ),
                       inline=True
                       ),
                     ),
                   secondary=True)

    ginfo_el = e(ui.Segment,
                 *((e(ui.Label,
                      e(ui.Icon, js_name="checkmark"),
                      tr(this, "ui.t-metadata-file", "Metadata file"),
                      title=tr(this, "ui.t-metadata-from-file", "Metadata was retrieved from file"),
                      color="green", basic=True,
                      className="right"),) if this.state.data.metadata_from_file else []),
                 *((e(ui.Label,
                      e(ui.Icon, js_name="warning circle"),
                      tr(this, "ui.t-already-exists", "Exists"),
                      color="orange", basic=True,
                      className="right"),) if this.state.data.exists else []),
                 e(gallerypropsview.GalleryProps,
                   data=gallery_data,
                   sources=this.state.data.sources,
                   update_data=this.on_update_data,
                   edit_mode=True,
                   new_mode=True,
                   single_tags=True,
                   ),
                 loading=this.state.submitting,
                 )
    pages_el = []
    if this.state.pages:
        for p in this.state.pages:
            pages_el.append(e(ui.Item,
                              e(ui.Item.Content,
                                e(ui.Item.Meta, e(ui.Label, p.number, color="blue"), e(ui.Label, p.js_name)),
                                e(ui.Item.Extra, p.path),
                                onDismiss=this.remove_page,
                                as_=ui.Message,
                                value=p.number,
                                color="red",
                                ),
                              key=p.number,
                              ),
                            )

    gpages_el = e(ui.Segment, e(ui.Label, tr(this, "ui.t-pages", "Pages"), e(ui.Label.Detail, len(this.state.pages)), attached="top"),
                  e(ui.Item.Group, pages_el, divided=True, relaxed=True, className="max-800-h"),
                  loading=this.state.submitting,)

    dirty = not utils.lodash_lang.isEmpty(gallery_data)

    return e("div",
             e(TitleChange, title=tr(this, "ui.t-create-gallery", "Create a gallery")),
             e(Prompt, when=dirty, message=tr(this, "ui.t-page-changes-prompt", "Are you sure?")),
             e(ui.Container,
                 e(ui.Form,
                   e(ui.Form.Group,
                     e(ui.Form.Input,
                       width=16,
                       fluid=True,
                       action={'color': 'yellow' if this.state.load_gallery_loading else 'teal',
                               'icon': e(ui.Icon, js_name='sync alternate',
                                         loading=this.state.load_gallery_loading)},
                       onChange=this.set_path,
                       placeholder=tr(this, "ui.t-load-gallery", "Load gallery"),
                       ),
                     ),
                   onSubmit=this.on_load_gallery_submit,
                   ),
                 options_el,
                 e(ui.Form,
                   *((e(ui.Divider, e(ui.Button, tr(this, "ui.t-submit", "Submit"), disabled=this.state.submitting,
                                      primary=True, js_type="submit"), horizontal=True),) if dirty else []),
                   ginfo_el,
                   gpages_el,
                   *((e(ui.Divider, e(ui.Button, tr(this, "ui.t-submit", "Submit"), disabled=this.state.submitting,
                                      primary=True, js_type="submit"), horizontal=True),) if dirty else []),
                   onSubmit=this.on_gallery_submit,
                   )
               ),
             )


CreateGallery = createReactClass({
    'displayName': 'CreateGallery',

    'getInitialState': lambda: {
        'data': {},
        'pages': [],
        'gallery_data': {},
        'load_gallery_path': '',
        'load_gallery_loading': False,
        'options': {'gallery.add_to_inbox': utils.storage.get('new_gallery.add_to_inbox', this.props.config['gallery.add_to_inbox'] if utils.defined(this.props.config['gallery.add_to_inbox']) else False),
                    },
        'submitting': False,
    },

    'load_gallery': load_gallery,
    'update_options': update_options,

    'on_update_data': creategallery_on_update_data,
    'update_data': utils.update_data,

    'on_add_to_inbox': lambda e, d: all((this.update_options('gallery.add_to_inbox', d.checked), utils.storage.set('new_gallery.add_to_inbox', d.checked))),
    'remove_page': lambda e, d: this.setState({'pages': utils.remove_from_list(this.state.pages, d.value, key='number')}),

    'on_load_gallery_submit': lambda e, d: this.load_gallery(),
    'set_path': lambda e, d: this.setState({'load_gallery_path': d.value}),

    'submit_gallery': submit_gallery,
    'on_gallery_submit': lambda: all((this.submit_gallery(),)),
    'on_submitted': lambda cmd: all((this.setState({'data': {},
                                                    'pages': [],
                                                    'gallery_data': {},
                                                    'new_data': {},
                                                    'submitting': False}), state.app.notif(this.submit_txt, level="success", icon="checkmark"))) if cmd.finished() else None,
    'componentDidUpdate': creategallery_update,
    'render': creategallery_render
})


def createcollection_render():
    return e("div",
             e(TitleChange, title=tr(this, "ui.t-create-collection", "Create a collection")),
             )


CreateCollection = createReactClass({
    'displayName': 'CreateCollection',

    'getInitialState': lambda: {
        'data': {},
    },

    'render': createcollection_render
})


def createpage_render():

    item_type = {'gallery': ItemType.Gallery,
                 'collection': ItemType.Collection}.get(this.props.match.params.item_type.lower(),
                                                        ItemType.Gallery)

    if item_type == ItemType.Gallery:
        el = e(CreateGallery, config=this.state.config, set_config=this.set_config)
    elif item_type == ItemType.Collection:
        el = e(CreateCollection, config=this.state.config, set_config=this.set_config)

    return e(ui.Container,
             e(ui.Container,
               e(ui.Button.Group,
                 e(ui.Button, tr(this, "general.db-item-gallery", "Gallery"),
                   value=ItemType.Gallery,
                   active=item_type == ItemType.Gallery,
                   primary=item_type == ItemType.Gallery,
                   as_=Link,
                   to="/manage/new/gallery",
                   ),
                 e(ui.Button.Or, text=tr(this, "ui.t-or", "Or")),
                 e(ui.Button, tr(this, "general.db-item-collection", "Collection"),
                   disabled=True,
                   value=ItemType.Collection,
                   active=item_type == ItemType.Collection,
                   primary=item_type == ItemType.Collection,
                   as_=Link,
                   to="/manage/new/collection",
                   ),
                 toggle=True,
                 ),
               textAlign="center"),
             e(ui.Divider, hidden=True),
             el
             )


CreatePage = createReactClass({
    'displayName': 'CreatePage',

    'getInitialState': lambda: {
        'config': {},
        'data': {},
        'item_type': this.props.item_type or ItemType.Gallery,
    },
    'set_item_type': lambda e, d: this.setState({'item_type': d.value}),
    'get_config': get_config,
    'set_config': set_config,

    'componentDidMount': lambda: all((this.get_config(cfg={'gallery.add_to_inbox': True,
                                                           }),)),

    'render': createpage_render
})

Page = createReactClass({
    'displayName': 'ManagePage',

    'componentWillMount': lambda: this.props.menu([
        e(ui.Menu.Item, js_name=tr(this, "ui.b-new", "New"), as_=NavLink,
          to="/manage/new", activeClassName="active"),
        e(ui.Menu.Item, js_name=tr(this, "ui.mi-scan", "Scan"), as_=NavLink,
          to="/manage/scan", activeClassName="active"),
    ], pointing=True),

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Segment,
                        e(Switch,
                            e(Route, path="/manage/new/:item_type(\w+)", component=CreatePage),
                            e(Route, path="/manage/scan", component=ScanPage),
                            e(Redirect, js_from="/manage/new", exact=True, to={'pathname': "/manage/new/gallery"}),
                            e(Redirect, js_from="/manage", exact=True, to={'pathname': "/manage/new"}),
                          ),
                        basic=True,
                        )
})
