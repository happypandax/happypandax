from src.react_utils import (e,
                             createReactClass,
                             Link)
from src.ui import ui, Slider, LabelAccordion, TitleChange
from src.i18n import tr
from src.state import state
from src.client import ItemType, ImageSize, client, Command
from src.single import galleryitem, thumbitem, collectionitem
from src.propsviews import gallerypropsview
from src.views import itemview
from src.props import galleryprops, simpleprops
from src import utils
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Date = None
__pragma__('noskip')


def get_config(data=None, error=None):
    if data is not None and not error:
        this.setState({"external_viewer": data['this.use_external_image_viewer']})
    elif error:
        state.app.notif("Failed to fetch config: {}".format(error), level="error")
    else:
        pass


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


__pragma__("notconv")


def get_item(ctx=None, data=None, error=None, force=False, only_gallery=False):
    if not this.mounted:
        return
    if data is not None and not error:
        this.setState({"data": data,
                       "loading": False,
                       "tags_data": js_undefined,
                       })

        if data.metatags.favorite:
            this.setState({"fav": 1})
        else:
            this.setState({"fav": 0})

        if data.grouping_id:
            this.setState({"loading_group": True})
            client.call_func("get_related_items", this.get_grouping,
                             item_type=ItemType.Grouping,
                             related_type=this.state.item_type,
                             item_id=data.grouping_id)
            client.call_func("get_related_items", this.get_status,
                             item_type=ItemType.Grouping,
                             related_type=ItemType.Status,
                             item_id=data.grouping_id)
        if data.language_id:
            this.setState({"loading_lang": True})
            client.call_func("get_item", this.get_lang,
                             item_type=ItemType.Language,
                             item_id=data.language_id)

        if data.category_id:
            this.setState({"loading_category": True})
            client.call_func("get_item", this.get_category,
                             item_type=ItemType.Category,
                             item_id=data.category_id)

        if not ctx.only_gallery:
            trash = data.metatags.trash

            if not trash and data.id:
                client.call_func("get_related_count", this.get_filter_count,
                                 related_type=ItemType.GalleryFilter,
                                 item_type=this.state.item_type,
                                 item_id=data.id)
                client.call_func("get_related_items", this.get_collection_data,
                                 related_type=ItemType.Collection,
                                 item_type=this.state.item_type,
                                 item_id=data.id)
                client.call_func("get_related_items", this.get_filters,
                                 item_type=ItemType.Gallery,
                                 related_type=ItemType.GalleryFilter,
                                 item_id=data.id)

                client.call_func("get_similar", this.get_similar,
                                 item_type=ItemType.Gallery,
                                 item_id=data.id, limit=30)
                this.setState({"similar_gallery_loading": True})

            this.setState({'same_artist_data': []})
            if not trash and len(data.artists):
                for a in list(data.artists)[:5]:
                    if a.id:
                        client.call_func("get_related_items", this.get_same_artist_data,
                                         related_type=ItemType.Gallery, item_id=a.id, item_type=ItemType.Artist,
                                         limit=10 if len(data.artists) > 1 else 30)

        this.update_menu(data)

    elif error:
        state.app.notif("Failed to fetch item ({})".format(this.state.id), level="error")
    else:
        ctx = {'only_gallery': only_gallery, }
        item_id = this.state.id
        if utils.defined(this.props.location):
            if this.props.location.state and this.props.location.state.gallery:
                if int(this.props.match.params.item_id) == this.props.location.state.gallery.id:
                    if not force:
                        this.get_item(ctx, this.props.location.state.gallery)
                        return
                    else:
                        item_id = this.props.match.params.item_id

        item = this.state.item_type
        if item and item_id:
            client.call_func("get_item", this.get_item, ctx=ctx, item_type=item, item_id=item_id)
            this.setState({'loading': True,
                           })


__pragma__('nokwargs')

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
        if new_data and (new_data['tags'] or new_data['taggable']['tags'] if new_data['taggable'] else None):
            tag_data = new_data['tags'] or new_data['taggable']['tags']
            del new_data['tags']
            del new_data['taggable']
            this.update_tags(new_data=tag_data)
        if new_data and new_data.id and utils.lodash_collection.size(new_data) > 1:
            client.call_func("update_item", this.update_item,
                             item_type=this.state.item_type,
                             item=new_data)


__pragma__('nokwargs')

__pragma__('kwargs')


def update_tags(data=None, error=None, new_data=None):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to update tags ({})".format(this.state.data.id), level="error")
    else:
        new_data = new_data or this.state.new_data
        if new_data:
            client.call_func("update_item_tags", this.update_tags,
                             item_type=this.state.item_type,
                             item_id=this.state.data.id,
                             tags=new_data)


__pragma__('nokwargs')


def get_grouping(data=None, error=None):
    if data is not None and not error:
        this.setState({"group_data": data, "loading_group": False})
    elif error:
        this.setState({"loading_group": False})
        state.app.notif("Failed to fetch grouping ({})".format(this.state.id), level="error")


def get_lang(data=None, error=None):
    if data is not None and not error:
        this.setState({"lang_data": data, "loading_lang": False})
    elif error:
        state.app.notif("Failed to fetch language ({})".format(this.state.id), level="error")


def get_category(data=None, error=None):
    if data is not None and not error:
        this.setState({"category_data": data, "loading_category": False})
    elif error:
        state.app.notif("Failed to fetch category ({})".format(this.state.id), level="error")


def get_filter_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"filter_count": data['count']})
    elif error:
        state.app.notif("Failed to fetch filter count ({})".format(this.state.id), level="error")


def get_filters(data=None, error=None):
    if data is not None and not error:
        this.setState({"filter_data": data})
    elif error:
        state.app.notif("Failed to fetch gallery filters ({})".format(this.state.id), level="error")


def get_collection_data(data=None, error=None):
    if data is not None and not error:
        this.setState({"collection_count": len(data), 'collection_data': data})
    elif error:
        state.app.notif("Failed to fetch collection data ({})".format(this.state.id), level="error")


def get_same_artist_data(data=None, error=None):
    if not this.mounted:
        return
    if data is not None and not error:
        g_id = this.state.data.id or 0
        items = [x for x in data if x.id != g_id]
        a_data = this.state.same_artist_data
        [items.append(x) for x in a_data if x.id != g_id]
        g_ids = []
        g_items = []
        for x in [x for x in items]:
            if x.id in g_ids:
                continue
            g_ids.append(x.id)
            g_items.append(x)
        this.setState({'same_artist_data': g_items})
    elif error:
        state.app.notif("Failed to fetch same artist data ({})".format(this.state.id), level="error")


__pragma__("tconv")


def get_similar_progress(cmd):
    p = cmd.get_progress()
    if p:
        this.setState({"similar_gallery_progress": p})


__pragma__("notconv")


def get_similar_value(cmd):
    if not this.mounted:
        return
    v = cmd.get_value()
    this.setState({"similar_gallery_data": v or [], 'similar_gallery_loading': False})


def get_similar(data=None, error=None):
    if data is not None and not error:
        cmd = Command(data)
        cmd.poll_until_complete(1000)
        cmd.poll_progress(callback=this.get_similar_progress)
        cmd.set_callback(this.get_similar_value)

    elif error:
        state.app.notif("Failed to fetch similar galleries ({})".format(this.state.id), level="error")


__pragma__("tconv")


def get_status(data=None, error=None):
    if data is not None and not error:
        if data:
            this.setState({"status_data": data[0]})
    elif error:
        state.app.notif("Failed to fetch status ({})".format(this.state.id), level="error")


__pragma__("notconv")


def toggle_external_viewer(e, d):
    v = not d.active
    this.setState({'external_viewer': v})
    utils.storage.set('external_viewer', v)


def gallery_favorite(e, d):
    e.preventDefault()
    this.setState({'fav': d.rating})
    if this.state.edit_mode:
        this.update_data(bool(d.rating), "metatags.favorite")
    else:
        this.update_metatags({'favorite': bool(d.rating)})
        this.get_item(only_gallery=True, force=True)


def gallery_rate(e, d):
    e.preventDefault()
    rating = d.rating
    if this.state.edit_mode:
        this.update_data(rating, "rating")
    else:
        if this.state.data.id:
            client.call_func("update_item", item_type=this.state.item_type,
                             item={'id': this.state.data.id, 'rating': rating})
        this.setState({'data': utils.update_object("rating", this.state.data, rating)})
        this.get_item(only_gallery=True, force=True)


def gallery_on_update(p_props, p_state):
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

            g = utils.JSONCopy(this.state.data)
            if g.tags:
                del g['tags']
            if g.taggable:
                del g['taggable']
            this.props.location.state.gallery = g
            this.props.history.js_replace(this.props.location)

    if any((
        p_state.edit_mode != this.state.edit_mode,
    )):
        this.update_menu()


__pragma__("tconv")


def page_willmount():
    this.update_menu()
    this.get_item() if not this.state.data else None
    this.get_config()


def page_willunmount():
    pass


def page_render():

    fav = this.state.fav
    title = ""
    item_id = this.state.id
    inbox = False
    trash = False
    date_upd = None
    date_read = None
    date_added = None
    titles = []
    title_data = None
    category_data = this.state.category_data
    if this.state.data:
        item_id = this.state.data.id
        if this.state.data.titles:
            titles = this.state.data.titles

        if this.state.data.last_updated:
            date_upd = this.state.data.last_updated
        if this.state.data.last_read:
            date_read = this.state.data.last_read
        if this.state.data.timestamp:
            date_added = this.state.data.timestamp
        if this.state.data.preferred_title:
            title = this.state.data.preferred_title.js_name
            title_data = this.state.data.preferred_title
        inbox = this.state.data.metatags.inbox
        trash = this.state.data.metatags.trash
        if not item_id:
            item_id = this.state.data.id

        if this.state.data.category:
            category_data = this.state.data.category

    series_data = []
    if this.state.group_data:
        series_data = this.state.group_data

    indicators = []
    if inbox:
        indicators.append(e(ui.Icon, js_name="inbox", size="big", title=tr(
            this, "ui.t-inboxed-gallery", "This gallery is in your inbox")))

    if trash:
        indicators.append(e(ui.Icon, js_name="trash", color="red", size="big",
                            title=tr(this, "ui.t-trashed-gallery", "This gallery is set to be deleted")))

    if this.state.category_data or this.state.edit_mode:
        indicators.append(e(galleryprops.Category,
                            data=category_data,
                            data_key="category",
                            update_data=this.update_data,
                            edit_mode=this.state.edit_mode,
                            basic=True, size="medium"))

    if this.state.loading or this.state.loading_group or this.state.loading_lang or this.state.loading_category:
        indicators.append(e(ui.Icon, js_name="sync alternate", color="blue", size="large",
                            loading=True))

    buttons = []
    external_view = []
    if utils.is_same_machine():
        external_view.append(e(ui.Button, icon="external", toggle=True, active=this.state.external_viewer,
                               title=tr(this, "ui.t-open-external-viewer", "Open in external viewer"), onClick=this.toggle_external_viewer))

    read_btn = {}
    read_btn['onClick'] = this.on_read
    if not this.state.external_viewer:
        read_btn['as'] = Link
        read_btn['to'] = {'pathname': "/item/gallery/{}/page/1".format(item_id), 'state': {'gallery': this.state.data}}

    buttons.append(
        e(ui.Grid.Row,
          e(ui.Grid.Column,
            e(ui.Button.Group,
              e(ui.Button, e(ui.Icon, js_name="bookmark outline"), tr(this, "ui.b-save-later", "Save for later")),
              e(ui.Button.Or, text="or"),
              e(ui.Button, tr(this, "ui.b-read", "Read"), primary=True, **read_btn),
              *external_view,
              ),
            textAlign="center",
            ),
          centered=True,
          ),
    )

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

    filter_accordion = []
    if this.state.filter_count:
        filter_items = []
        for f in this.state.filter_data:
            filter_items.append(e(ui.List.Item,
                                  e(ui.List.Icon, js_name="filter"),
                                  e(ui.List.Content, f['name'],),
                                  as_=Link, to=utils.build_url("/library",
                                                               {'filter_id': f['id']},
                                                               keep_query=False),
                                  ))
        filter_accordion.append(e(ui.Accordion,
                                  panels=[
                                      {
                                          'title': {
                                              'content': e(ui.Label,
                                                           tr(this, "ui.h-included-gallery-filters",
                                                              "Included in {} gallery filter".format(
                                                                  this.state.filter_count),
                                                              count=this.state.filter_count),
                                                           color="teal",),
                                              'key': 't-1',
                                          },
                                          'content': {
                                              'content': e(ui.List, *filter_items,
                                                           animated=True,
                                                           link=True,
                                                           celled=True,
                                                           relaxed=True),
                                              'key': 't-2',
                                          },
                                          'key': 'c-1'
                                      }
                                  ],
                                  ))

    series_accordion = []
    if len(series_data) > 1 or this.state.edit_mode:
        series_accordion.append(e(ui.Grid.Row, e(ui.Grid.Column,
                                                 e(Slider, [e(galleryitem.Gallery, data=x, className="small-size", key=x.id) for x in series_data],
                                                   loading=this.state.loading_group,
                                                   basic=False,
                                                   secondary=True,
                                                   sildesToShow=4,
                                                   color="blue",
                                                   label=tr(this, "ui.t-series", "Series")),
                                                 )))

    collection_accordion = []

    if this.state.collection_count or this.state.edit_mode:
        collection_data = this.state.collection_data
        collection_accordion.append(e(ui.Grid.Row,
                                      e(ui.Grid.Column,
                                        e(LabelAccordion,
                                          e(Slider,
                                            [e(collectionitem.Collection, data=x, className="small-size", key=x.id)
                                                for x in collection_data],
                                            secondary=True,
                                            sildesToShow=4),
                                          label=tr(this, "ui.h-appears-in-collection",
                                                   "Appears in {} collection".format(this.state.collection_count),
                                                   count=this.state.collection_count),
                                          color="teal",
                                          cfg_suffix=this.cfg_suffix + 'collection',
                                          default_open=True
                                          )
                                        )
                                      )
                                    )

    same_artist_accordion = []

    same_artist_data = this.state.same_artist_data
    if len(same_artist_data) > 1:
        same_artist_accordion.append(e(ui.Grid.Row,
                                       e(ui.Grid.Column,
                                         e(LabelAccordion,
                                           e(Slider,
                                             [e(galleryitem.Gallery, data=x, className="small-size", key=x.id)
                                              for x in same_artist_data],
                                             secondary=True,
                                             sildesToShow=4),
                                           label=tr(
                                               this,
                                               "ui.h-more-same-artist",
                                               "More from same artist",
                                               count=len(
                                                   this.state.data.artists)),
                                             color="violet",
                                             cfg_suffix=this.cfg_suffix + 'same_artist',
                                             default_open=True
                                           )
                                         )
                                       )
                                     )

    similar_galleries = []

    if not trash and (len(this.state.similar_gallery_data) or this.state.similar_gallery_loading):
        similar_gallery_data = this.state.similar_gallery_data
        similar_slider_el = e(Slider,
                              [e(galleryitem.Gallery, data=x, className="small-size", key=x.id)
                               for x in similar_gallery_data],
                              secondary=True,
                              sildesToShow=4)
        similar_progress_el = e(ui.Segment, e(ui.Progress,
                                              size="small",
                                              active=True,
                                              total=this.state.similar_gallery_progress.max or js_undefined,
                                              value=this.state.similar_gallery_progress.value,
                                              progress="value",
                                              autoSuccess=True),
                                basic=True)
        similar_galleries.append(e(ui.Grid.Row,
                                   e(ui.Grid.Column,
                                     e(LabelAccordion,
                                       similar_progress_el if this.state.similar_gallery_loading else similar_slider_el,
                                       label=tr(this, "ui.h-more-like-this", "More like this"),
                                       cfg_suffix=this.cfg_suffix + 'similar',
                                       default_open=True
                                       )
                                     )
                                   )
                                 )

    return e(ui.Grid,
             e(TitleChange, title=title if title else tr(this, "general.db-item-gallery", "Gallery")),
             # e(Prompt, when=this.state.edit_mode and bool(this.state.new_data) and not utils.lodash_lang.isEmpty(this.state.new_data),
             #  message=tr(this, "ui.t-page-changes-prompt", "Are you sure?")),
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
                   e(ui.Grid.Row,
                     *filter_accordion,
                     ),
                   centered=True, verticalAlign="top"),
                 ),
               e(ui.Grid.Column,
                 e(ui.Grid,
                   e(ui.Grid.Row,
                     e(ui.Grid.Column, e(ui.Rating, icon="heart", size="massive", rating=fav, onRate=this.favorite),
                       floated="right", className="no-margins"),
                     e(ui.Grid.Column, *indicators, floated="right", textAlign="right", className="no-margins"),
                     columns=2,
                     verticalAlign="middle",
                     ),
                   e(ui.Grid.Row,
                     e(ui.Grid,
                       e(ui.Grid.Row,
                         e(ui.Grid.Column,
                           e(galleryprops.Titles,
                             data=titles,
                             preferred=title_data,
                             edit_mode=this.state.edit_mode,
                             update_data=this.update_data,
                             data_key="titles",
                             size="small"))),
                       e(ui.Grid.Row,
                         e(ui.Grid.Column,
                           e(gallerypropsview.GalleryProps,
                             data=this.state.data,
                             main=True,
                             status=this.state.status_data,
                             language=this.state.lang_data,
                             category=this.state.category_data,
                             tags=this.state.tags_data,
                             on_tags=this.on_tags,
                             size="large",
                             update_data=this.update_data,
                             on_rate=this.rate,
                             edit_mode=this.state.edit_mode,
                             submitted_data=this.state.submitted_data,
                             ))),
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
               # loading=this.state.loading,
               basic=True,
               ),
             e(ui.Grid.Row,
               e(ui.Grid.Column,
                 e(simpleprops.DateLabel,
                   update_data=this.update_data,
                   data_key="timestamp",
                   edit_mode=this.state.edit_mode,
                   text=tr(this, "ui.t-date-added", "Date added"),
                   data=date_added, format="LLL"),
                 textAlign="center"),
               e(ui.Grid.Column,
                 e(simpleprops.DateLabel,
                   update_data=this.update_data,
                   data_key="last_read",
                   edit_mode=this.state.edit_mode,
                   text=tr(this, "ui.t-last-read", "Last read"),
                   data=date_read, format="LLL"),
                 textAlign="center"),
               e(ui.Grid.Column,
                 e(simpleprops.DateLabel,
                   update_data=this.update_data,
                   data_key="last_updated",
                   edit_mode=this.state.edit_mode,
                   text=tr(this, "ui.t-last-updated", "Last updated"),
                   data=date_upd, format="LLL",
                   disabled=True if this.state.edit_mode else False),
                 textAlign="center"),
               columns=3
               ),
             *series_accordion,
             *collection_accordion,
             *same_artist_accordion,
             *similar_galleries,
             e(ui.Grid.Row, e(ui.Grid.Column, e(itemview.ItemView,
                                                history=this.props.history,
                                                location=this.props.location,
                                                item_id=item_id,
                                                item_type=ItemType.Gallery,
                                                related_type=ItemType.Page,
                                                view_filter=None,
                                                label=tr(this, "ui.t-pages", "Pages"),
                                                config_suffix=this.cfg_suffix,
                                                toggle_config=this.toggle_pages_config,
                                                visible_config=this.state.visible_page_cfg,
                                                container=True, secondary=True))),
             stackable=True,
             container=True,
             )


__pragma__("notconv")


Page = createReactClass({
    'displayName': 'GalleryPage',

    'cfg_suffix': "gallerypage",

    'getInitialState': lambda: {'id': int(this.props.match.params.item_id),
                                'data': this.props.data,
                                'new_data': None,
                                'old_data': None,
                                'fav': 0,
                                'category_data': this.props.category_data or {},
                                'lang_data': this.props.lang_data or {},
                                'status_data': this.props.status_data or {},
                                'group_data': this.props.group_data or [],
                                'tags_data': this.props.tags_data,
                                'item_type': ItemType.Gallery,
                                'loading': True,
                                'loading_group': False,
                                'loading_lang': False,
                                'loading_category': False,
                                'edit_mode': False,
                                'submitted_data': False,
                                'external_viewer': utils.storage.get("external_viewer", False),
                                'send_to_recycle': True,
                                'delete_files': False,
                                'visible_page_cfg': False,
                                'collection_count': this.props.collection_count or 0,
                                'collection_data': [],
                                'filter_count': this.props.filter_count or 0,
                                'filter_data': [],
                                'similar_gallery_progress': {},
                                'similar_gallery_loading': True,
                                'similar_gallery_data': [],
                                'same_artist_data': [],
                                },

    'update_menu': update_menu,
    'update_item': update_item,
    'update_tags': update_tags,
    'get_item': get_item,
    'get_grouping': get_grouping,
    'get_lang': get_lang,
    'get_category': get_category,
    'get_status': get_status,
    'get_filter_count': get_filter_count,
    'get_filters': get_filters,
    'get_similar': get_similar,
    'get_similar_value': get_similar_value,
    'get_similar_progress': get_similar_progress,
    'get_collection_data': get_collection_data,
    'get_same_artist_data': get_same_artist_data,
    'get_config': get_config,
    'update_metatags': galleryitem.update_metatags,
    'open_external': galleryitem.open_external,
    'read_event': galleryitem.read_event,

    'update_data': utils.update_data,

    'favorite': gallery_favorite,
    'rate': gallery_rate,
    'send_to_library': lambda e, d: all((this.update_metatags({'inbox': False}),
                                         e.preventDefault())),
    'send_to_trash': lambda e, d: all((this.update_metatags({'trash': True}),
                                       e.preventDefault())),
    'restore_from_trash': lambda e, d: all((this.update_metatags({'trash': False}),
                                            e.preventDefault())),
    'read_later': lambda e, d: all((this.update_metatags({'readlater': True}),
                                    e.preventDefault())),

    'on_edit': lambda e, d: all((this.setState({'edit_mode': True, 'new_data': {}, 'submitted_data': False, 'old_data': utils.JSONCopy(this.state.data)}), )),
    'on_cancel_edit': lambda e, d: all((this.setState({'data': this.state.old_data}) if this.state.old_data else None, this.setState({'edit_mode': False, 'old_data': None}))),
    'on_save_edit': lambda e, d: all((this.setState({'edit_mode': False, 'submitted_data': True, 'old_data': None}),
                                      this.update_item(), this.get_item(only_gallery=True, force=True))),

    'on_read': lambda e, d: all((this.read_event(e, d),
                                 this.open_external(e, d) if this.state.external_viewer else None,
                                 this.get_item(force=True))),

    'on_tags': lambda a: this.setState({'tags_data': a}),
    'toggle_pages_config': lambda a: this.setState({'visible_page_cfg': not this.state.visible_page_cfg}),
    'toggle_external_viewer': toggle_external_viewer,

    'componentWillMount': page_willmount,
    'componentWillUnmount': page_willunmount,
    'componentDidUpdate': gallery_on_update,

    'render': page_render
})
