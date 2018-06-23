from src.react_utils import (e,
                             createReactClass)
from src.ui import ui, TitleChange, DateLabel
from src.i18n import tr
from src.state import state
from src.single import thumbitem
from src.client import ItemType, ImageSize, client
from src.propsviews import collectionpropsview
from src.views import itemview
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

__pragma__('kwargs')


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

            if len(menu_items):
                this.props.menu(menu_items)

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


__pragma__('nokwargs')


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


def collection_on_update(p_props, p_state):
    if p_props.location.pathname != this.props.location.pathname:
        this.setState({'id': int(this.props.match.params.item_id)})

    if any((
        p_state.id != this.state.id,
    )):
        this.get_item()


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
                 e(DateLabel, tr(this, "ui.t-date-added", "Date added"), timestamp=date_added, format="LLL"),
                 textAlign="center"),
               e(ui.Grid.Column,
                 e(DateLabel, tr(this, "ui.t-last-updated", "Last updated"), timestamp=date_upd, format="LLL"),
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
                                'rating': 0,
                                'fav': 0,
                                'item_type': ItemType.Collection,
                                'category_data': this.props.category_data or {},
                                'gallery_count': 0,
                                'loading': True,
                                'loading_group': True,
                                'send_to_recycle': True,
                                'visible_gallery_cfg': False,
                                },

    'get_item': get_item,
    'get_category': get_category,

    'toggle_galleries_config': lambda a: this.setState({'visible_gallery_cfg': not this.state.visible_gallery_cfg}),

    'componentWillMount': lambda: all(((this.get_item() if not this.state.data else None),
                                       )),
    'componentDidUpdate': collection_on_update,

    'render': page_render
})
