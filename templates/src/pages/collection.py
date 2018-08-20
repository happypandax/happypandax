from src.react_utils import (e,
                             createReactClass)
from src.ui import ui, TitleChange
from src.i18n import tr
from src.state import state
from src.single import thumbitem
from src.client import ItemType, ImageSize, client
from src.propsviews import collectionpropsview
from src.views import itemview
from src.props import simpleprops
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

__pragma__('kwargs')
__pragma__("tconv")


def update_menu(data={}):
    if not data and this.state.data:
        data = this.state.data
    if data.id:
        inbox = data.metatags.inbox
        trash = data.metatags.trash
        menu_items = []
        menu_left = []
        min_width = 768
        btn_size = "small"
        if inbox:
            menu_left.append(e(ui.Responsive, e(ui.Button,
                                                e(ui.Icon, js_name="grid layout"),
                                                tr(this, "ui.b-send-library", "Send to Library"),
                                                onClick=this.send_to_library,
                                                color="green", basic=True),
                               as_=ui.Menu.Item,
                               minWidth=min_width,
                               ))
        menu_items.append(e(ui.Menu.Menu, *menu_left))
        menu_right = []
        menu_right.append(
            e(ui.Responsive,
                e(ui.Button, e(ui.Icon, js_name="trash" if not trash else "reply"),
                  tr(this, "ui.b-send-trash", "Send to Trash") if not trash else tr(this, "ui.b-restore", "Restore"),
                  color="red" if not trash else "teal", basic=True, onClick=this.send_to_trash if not trash else this.restore_from_trash),
                as_=ui.Menu.Item,
                minWidth=min_width,
              ))

        if trash:
            menu_right.append(
                e(ui.Responsive,
                    e(ui.Button.Group,
                        e(ui.Button,
                          e(ui.Icon, js_name="close"), tr(this, "ui.b-delete", "Delete"), color="red"),
                        e(ui.Button, icon="remove circle", toggle=True, active=this.state.delete_files,
                          title=tr(this, "ui.t-delete-files", "Delete files")),
                        e(ui.Button, icon="recycle", toggle=True, active=this.state.send_to_recycle,
                          title=tr(this, "ui.t-send-recycle-bin", "Send files to Recycle Bin"),
                          ),
                        basic=True,
                        size=btn_size
                      ),
                    as_=ui.Menu.Item,
                    minWidth=min_width,
                  ))

        menu_right.append(e(ui.Responsive,
                            e(ui.Button,
                              e(ui.Icon, js_name="edit") if not this.state.edit_mode else e(ui.Icon, js_name="delete"),
                              tr(this, "ui.b-edit", "Edit") if not this.state.edit_mode else tr(this, "ui.b-cancel", "Cancel"),
                              onClick=this.on_edit if not this.state.edit_mode else this.on_cancel_edit,
                              basic=True,
                              size=btn_size),
                            as_=ui.Menu.Item,
                            minWidth=min_width,
                            ))
        if this.state.edit_mode:
            menu_right.append(e(ui.Responsive,
                                e(ui.Button,
                                  e(ui.Icon, js_name="checkmark"),
                                  tr(this, "ui.b-save", "Save"),
                                  onClick=this.on_save_edit,
                                  color="green",
                                  size=btn_size),
                                as_=ui.Menu.Item,
                                minWidth=min_width,
                                ))

        menu_items.append(e(ui.Menu.Menu, *menu_right, position="right"))

        if len(menu_items):
            this.props.menu(menu_items, fixed=this.state.edit_mode)

    else:
        this.props.menu(e(ui.Menu.Menu))


def update_metatags(mtags):
    if this.state.data:
        client.call_func("update_metatags", None, item_type=this.state.item_type,
                         item_id=this.state.data.id, metatags=mtags)
        d = utils.JSONCopy(this.state.data)
        d.metatags = dict(d.metatags)
        d.metatags.update(mtags)
        this.setState({'data': d})


__pragma__("notconv")
__pragma__('nokwargs')


def get_item(data=None, error=None):
    if data is not None and not error:
        this.setState({"data": data,
                       "loading": False,
                       })
        if data.metatags.favorite:
            this.setState({"fav": 1})

        if data.category_id:
            client.call_func("get_item", this.get_category,
                             item_type=ItemType.Category,
                             item_id=data.category_id)

        if data.id:
            client.call_func("get_related_count", this.get_gallery_count,
                             related_type=ItemType.Gallery,
                             item_type=this.state.item_type,
                             item_id=data.id)

        if data.id:
            inbox = data.metatags.inbox
            trash = data.metatags.trash
            menu_items = []
            menu_left = []
            min_width = 768
            if inbox:
                menu_left.append(e(ui.Responsive, e(ui.Button, e(ui.Icon, js_name="grid layout"), tr(this, "ui.b-send-library", "Send to Library"), color="green", basic=True),
                                   as_=ui.Menu.Item,
                                   minWidth=min_width,
                                   ))
            menu_items.append(e(ui.Menu.Menu, *menu_left))
            menu_right = []
            menu_right.append(
                e(ui.Responsive,
                  e(ui.Button, e(ui.Icon, js_name="trash" if not trash else "reply"),
                    tr(this, "ui.b-send-trash", "Send to Trash") if not trash else tr(this, "ui.b-restore", "Restore"),
                    color="red" if not trash else "teal", basic=True),
                  as_=ui.Menu.Item,
                  minWidth=min_width,
                  ))

            if trash:
                menu_right.append(
                    e(ui.Responsive,
                      e(ui.Button.Group,
                          e(ui.Button,
                            e(ui.Icon, js_name="close"), tr(this, "ui.b-delete", "Delete"), color="red"),
                          e(ui.Button, icon="remove circle outline", toggle=True, active=this.state.delete_files,
                            title=tr(this, "ui.t-delete-files", "Delete files")),
                          e(ui.Button, icon="recycle", toggle=True, active=this.state.send_to_recycle,
                            title=tr(this, "ui.t-send-recycle-bin", "Send files to Recycle Bin")),
                          basic=True,
                        ),
                      as_=ui.Menu.Item,
                      minWidth=min_width,
                      ))

            menu_right.append(e(ui.Responsive,
                                e(ui.Button, e(ui.Icon, js_name="edit"), tr(this, "ui.b-edit", "Edit"), basic=True),
                                as_=ui.Menu.Item,
                                minWidth=min_width,
                                ))

            menu_items.append(e(ui.Menu.Menu, *menu_right, position="right"))

        this.update_menu(data)

    elif error:
        state.app.notif("Failed to fetch item ({})".format(this.state.id), level="error")
    else:
        if utils.defined(this.props.location):
            if this.props.location.state and this.props.location.state.collection:
                if int(this.props.match.params.item_id) == this.props.location.state.collection.id:
                    this.get_item(this.props.location.state.collection)
                    return
        item = this.state.item_type
        item_id = this.state.id
        if item and item_id:
            client.call_func("get_item", this.get_item, item_type=item, item_id=item_id)
            this.setState({'loading': True})


def get_gallery_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"gallery_count": data['count']})
    elif error:
        state.app.notif("Failed to fetch gallery count ({})".format(this.state.id), level="error")


def get_category(data=None, error=None):
    if data is not None and not error:
        this.setState({"category_data": data})
    elif error:
        state.app.notif("Failed to fetch category ({})".format(this.state.id), level="error")


__pragma__('kwargs')


def update_item(data=None, error=None, new_data=None):
    if data is not None and not error:
        if data:
            state.app.notif(tr(None, "ui.t-updated", "Updated!"), level="success")
        else:
            state.app.notif(tr(None, "ui.t-updated-fail", "Failed!"), level="warning")
        if this.state.new_data:
            this.setState({'new_data': None})
    elif error:
        state.app.notif("Failed to update item ({})".format(this.state.id), level="error")
    else:
        new_data = new_data or this.state.new_data
        if new_data and new_data.id and utils.lodash_collection.size(new_data) > 1:
            client.call_func("update_item", this.update_item,
                             item_type=this.state.item_type,
                             item=new_data)


__pragma__('nokwargs')


def collection_favorite(e, d):
    e.preventDefault()
    this.setState({'fav': d.rating})
    if this.state.edit_mode:
        this.update_data(bool(d.rating), "metatags.favorite")
    else:
        this.update_metatags({'favorite': bool(d.rating)})
        this.get_item(only_gallery=True, force=True)


def collection_on_update(p_props, p_state):
    if p_props.location.pathname != this.props.location.pathname:
        this.setState({'id': int(this.props.match.params.item_id)})

    if any((
        p_state.id != this.state.id,
    )):
        this.get_item()

    if any((
        p_state.data != this.state.data,
    )):
        this.update_menu()
        if this.props.location:
            c = utils.JSONCopy(this.state.data)
            this.props.location.state.collection = c
            this.props.history.js_replace(this.props.location)

    if any((
        p_state.edit_mode != this.state.edit_mode,
    )):
        this.update_menu()


__pragma__("tconv")


def page_render():

    fav = this.state.fav
    title = ""
    item_id = this.state.id
    inbox = False
    trash = False
    date_upd = None
    date_added = None
    if this.state.data:
        item_id = this.state.data.id

        if this.state.data.last_updated:
            date_upd = this.state.data.last_updated
        if this.state.data.timestamp:
            date_added = this.state.data.timestamp
        if this.state.data.js_name:
            title = this.state.data.js_name
        inbox = this.state.data.metatags.inbox
        trash = this.state.data.metatags.trash
        if not item_id:
            item_id = this.state.data.id

    indicators = []

    if this.state.category_data:
        indicators.append(e(ui.Label, this.state.category_data.js_name, basic=True, size="large"))

    if inbox:
        indicators.append(e(ui.Icon, js_name="inbox", size="big", title=tr(
            this, "ui.t-inboxed-collection", "This collection is in your inbox")))

    if trash:
        indicators.append(e(ui.Icon, js_name="trash", color="red", size="big",
                            title=tr(this, "ui.t-trashed-collection", "This collection is set to be deleted")))

    buttons = []

    if inbox:
        buttons.append(
            e(ui.Responsive,
              e(ui.Grid.Column,
                e(ui.Button,
                    e(ui.Icon, js_name="grid layout"), tr(this, "ui.b-send-library", "Send to Library"), color="green"),
                textAlign="center",
                ),
              centered=True,
                as_=ui.Grid.Row,
                maxWidth=767
              ),
        )

    buttons.append(
        e(ui.Responsive,
          e(ui.Grid.Column,
            e(ui.Button,
              e(ui.Icon, js_name="trash" if not trash else "reply"),
              tr(this, "ui.b-send-trash", "Send to Trash") if not trash else tr(this, "ui.b-restore", "Restore"),
              color="red" if not trash else "grey"),
            textAlign="center",
            ),
          divided=True,
            as_=ui.Grid.Row,
            maxWidth=767
          ),
    )

    if trash:
        buttons.append(
            e(ui.Responsive,
              e(ui.Grid.Column,
                e(ui.Button.Group,
                  e(ui.Button,
                    e(ui.Icon, js_name="close"), tr(this, "ui.b-delete", "Delete"), color="red"),
                  e(ui.Button, icon="remove circle outline", toggle=True, active=this.state.delete_files,
                    title=tr(this, "ui.t-delete-files", "Delete files")),
                  e(ui.Button, icon="recycle", toggle=True, active=this.state.send_to_recycle,
                    title=tr(this, "ui.t-send-recycle-bin", "Send files to Recycle Bin"))
                  ),
                textAlign="center",
                ),
              centered=True,
              as_=ui.Grid.Row,
              maxWidth=767
              ))

    return e(ui.Grid,
             e(TitleChange, title=title if title else tr(this, "general.db-item-collection", "Collection")),
             e(ui.Grid.Row, e(ui.Grid.Column, e(ui.Breadcrumb, icon="right arrow",))),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(ui.Grid, e(ui.Grid.Row,
                              e(ui.Grid.Column,
                                e(thumbitem.Thumbnail,
                                  size_type=ImageSize.Big,
                                  item_type=this.state.item_type,
                                  item_id=item_id,
                                  size="medium",
                                  shape="rounded",
                                  centered=True,
                                  bordered=True,),
                                tablet=10, mobile=6,
                                ),
                              centered=True,
                              ),
                   e(ui.Divider, fitted=True),
                   *buttons,
                   centered=True, verticalAlign="top"),
                 ),
               e(ui.Grid.Column,
                 e(ui.Grid,
                   e(ui.Grid.Row,
                     e(ui.Grid.Column, e(ui.Rating, icon="heart", size="massive",
                                         rating=fav), floated="right", className="no-margins"),
                     e(ui.Grid.Column, *indicators, floated="right", textAlign="right", className="no-margins"),
                     columns=2,
                     ),
                   e(ui.Grid.Row,
                     e(ui.Grid,
                       e(ui.Grid.Row, e(ui.Grid.Column, e(ui.Header, title, as_="h3"), textAlign="center")),
                       e(ui.Grid.Row, e(collectionpropsview.CollectionProps, data=this.state.data,
                                        category=this.state.category_data,
                                        gallery_count=this.state.gallery_count)),
                       stackable=True,
                       padded=False,
                       relaxed=True,
                       ),
                     ),
                   divided="vertically",
                   ),
                 ),
               columns=2,
               as_=ui.Segment,
               basic=True,
               ),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(simpleprops.DateLabel, text=tr(this, "ui.t-date-added", "Date added"), data=date_added, format="LLL"),
                 textAlign="center"),
               e(ui.Grid.Column,
                 e(simpleprops.DateLabel, text=tr(this, "ui.t-last-updated", "Last updated"), data=date_upd, format="LLL"),
                 textAlign="center"),
               columns=2
               ),
             e(ui.Grid.Row, e(ui.Grid.Column, e(itemview.ItemView,
                                                history=this.props.history,
                                                location=this.props.location,
                                                item_id=item_id,
                                                item_type=this.state.item_type,
                                                related_type=ItemType.Gallery,
                                                view_filter=None,
                                                label=tr(this, "ui.t-galleries", "Galleries"),
                                                config_suffix=this.cfg_suffix,
                                                toggle_config=this.toggle_galleries_config,
                                                visible_config=this.state.visible_gallery_cfg,
                                                show_search=True,
                                                # show_filterdropdown=True,
                                                show_sortdropdown=True,
                                                container=True,
                                                secondary=True))),
             stackable=True,
             container=True,
             )


__pragma__("notconv")

Page = createReactClass({
    'displayName': 'CollectionPage',

    'cfg_suffix': "collectionpage",

    'getInitialState': lambda: {'id': int(this.props.match.params.item_id),
                                'data': this.props.data,
                                'new_data': None,
                                'old_data': None,
                                'rating': 0,
                                'fav': 0,
                                'item_type': ItemType.Collection,
                                'category_data': this.props.category_data or {},
                                'gallery_count': 0,
                                'loading': True,
                                'loading_group': True,
                                'edit_mode': False,
                                'submitted_data': False,
                                'send_to_recycle': True,
                                'visible_gallery_cfg': False,
                                },

    'update_metatags': update_metatags,
    'update_data': utils.update_data,
    'update_menu': update_menu,
    'update_item': update_item,
    'get_item': get_item,
    'get_category': get_category,

    'favorite': collection_favorite,

    'send_to_library': lambda e, d: all((this.update_metatags({'inbox': False}),
                                         e.preventDefault())),
    'send_to_trash': lambda e, d: all((this.update_metatags({'trash': True}),
                                       e.preventDefault())),
    'restore_from_trash': lambda e, d: all((this.update_metatags({'trash': False}),
                                            e.preventDefault())),

    'on_edit': lambda e, d: all((this.setState({'edit_mode': True, 'new_data': {}, 'submitted_data': False, 'old_data': utils.JSONCopy(this.state.data)}), )),
    'on_cancel_edit': lambda e, d: all((this.setState({'data': this.state.old_data}) if this.state.old_data else None, this.setState({'edit_mode': False, 'old_data': None}))),
    'on_save_edit': lambda e, d: all((this.setState({'edit_mode': False, 'submitted_data': True, 'old_data': None}),
                                      this.update_item(), this.get_item(only_gallery=True, force=True))),

    'toggle_galleries_config': lambda a: this.setState({'visible_gallery_cfg': not this.state.visible_gallery_cfg}),

    'componentWillMount': lambda: all(((this.get_item() if not this.state.data else None),
                                       this.update_menu(),
                                       )),
    'componentDidUpdate': collection_on_update,

    'render': page_render
})
