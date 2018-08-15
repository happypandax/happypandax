import math
from src.react_utils import (h,
                             e,
                             createReactClass)
from src import utils
from src.state import state
from src.ui import ui, RemovableItem
from src.i18n import tr
from src.single import artistitem, parodyitem, circleitem
from src.client import ItemType, ItemSort, client
from src.props import simpleprops
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')
__pragma__('alias', 'js_input', 'input')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

def get_db_artists(data=None, error=None):
    if data is not None and not error:
        new_data = []
        old_data = this.props.data or this.state.data
        if old_data and len(old_data):
            new_data.extend(old_data)
        new_data.extend(data)
        this.setState({"data": new_data, 'loading': False, 'loading_more': False})
    elif error:
        state.app.notif("Failed to fetch artists", level="error")
        this.setState({'loading': False})
    else:
        client.call_func("search_items", this.get_items,
                         item_type=this.state.item_type,
                         search_query=this.state.search_query,
                         sort_by=ItemSort.ArtistName,
                         offset=this.state.limit * (this.state.page - 1),
                         limit=this.state.limit)

def get_artists_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"item_count": data['count']})
    elif error:
        state.app.notif("Failed to fetch artist count", level="error")
    else:
        client.call_func("get_count", this.get_items_count, item_type=this.state.item_type)


def get_more():
    pages = math.ceil(this.state.item_count / this.state.limit)
    if this.state.page < pages or not this.state.item_count:
        next_page = int(this.state.page) + 1
        this.setState({'page': next_page,
                       'loading_more': True})
        this.get_items()

def artistselector_update(p_p, p_s):
    if any((
        p_s.search_query != this.state.search_query,
        p_s.page != this.state.page
    )):
        this.get_items()

    if any((
        p_s.search_query != this.state.search_query,
    )):
        this.get_items_count()
        this.setState({'data': []})

def artistselector_on_item_remove(e, d):
    e.preventDefault()
    tid = e.target.dataset.id
    data = this.state.selected
    if tid and data:
        tid = int(tid)
        ndata = utils.remove_from_list(data, tid, key="id")
        this.setState({'selected': ndata})

def artistselector_on_item(e, data):
    selected = this.state.selected
    selected_ids = [a.id for a in selected]
    if data.id in selected_ids:
        selected = utils.remove_from_list(selected, data)
    else:
        selected = utils.update_object(None, this.state.selected, data, op="append", unique=lambda a,b:a['id']==b['id'])
    this.setState({'selected': selected})

def artistselector_on_submit(e, d):
    if this.props.onSubmit:
        this.props.onSubmit(e, this.state.selected)
    if this.props.onClose:
        this.props.onClose()

def artistselector_render():
    data = this.props.data or this.state.data
    selected = this.state.selected
    on_remove = this.on_item_remove
    top_el = e(ui.Grid,
               e(ui.Grid.Row,
                 e(ui.Grid.Column,
                    e(ui.Button, tr(this, "ui.t-select", "select"),
                      onClick=this.on_submit,
                      floated="right",
                      size="small",
                      primary=True) if len(selected) else None,
                   e(ui.Input,
                    size="mini",
                    defaultValue=this.state.search_query,
                    icon='search',
                    fluid=True,
                    onChange=this.update_search),
                   ),
                 ),
               e(ui.Grid.Row,
                 e(ui.Grid.Column,
                   e(ui.Label.Group,
                       [e(artistitem.ArtistLabel,
                             data=a,
                             key=a.id,
                             showRemove=True,
                             onRemove=on_remove
                            ) for a in selected]
                     )
                   )
                 )
               )

    selected_ids = [a.id for a in selected]
    if this.props.defaultSelected:
        defaultSelected = this.props.defaultSelected
        selected_ids.extend([a.id for a in defaultSelected])
    a_els = []
    if data:
        for a in data:
            a_els.append(e(artistitem.ArtistItem,
                         data=a,
                         active=a.id in selected_ids,
                         key=a.id,
                         selection=True,
                         onClick=this.on_item,
                        )
                        )
    if len(a_els):
        a_els.append(e(ui.Segment,
                       e(ui.Visibility,
                         context=this.state.context_el,
                        onTopVisible=this.get_more,
                        once=False,
                        fireOnMount=True,
                        ),
                        key="inf",
                        basic=True,
                        loading=this.state.loading_more,
                        ))

    els = e(ui.List, a_els,
            divided=True,
            relaxed=True,
            selection=True,
            link=True,
            size=this.props.size if this.props.size else "small",
            className="max-600-h min-500-h " + this.props.className if this.props.className else "max-600-h min-500-h",
            verticalAlign="middle")

    return e(ui.Segment,
             top_el,
             e(ui.Ref,
                els,
                innerRef=this.get_context_el,
               ),
             basic=True,
             loading=this.state.loading,
             )

ArtistSelector = createReactClass({
    'displayName': 'ArtistSelector',

    'getInitialState': lambda: {
                                'data': this.props.data or [],
                                'selected': [],
                                'loading': False,
                                'loading_more': False,
                                'limit': 20,
                                'search_query': this.props.search_query or "",
                                'item_count': 0,
                                'page': 1,
                                'item_type': ItemType.Artist,
                                'context_el': None,
                                },
    'on_item': artistselector_on_item,
    'on_item_remove': artistselector_on_item_remove,
    'on_submit': artistselector_on_submit,
    'get_items': get_db_artists,
    'get_items_count': get_artists_count,
    'get_context_el': lambda n: this.setState({'context_el': n}),
    'update_search': lambda e, d: all((this.setState({'search_query': d.value, 'page': 1}),
                                       this.setState({'loading': True}))),
    'get_more': get_more,
    'componentDidMount': lambda: all((this.get_items(), this.get_items_count(), this.setState({'loading': True}))),
    'componentDidUpdate': artistselector_update,
    'render': artistselector_render
})
