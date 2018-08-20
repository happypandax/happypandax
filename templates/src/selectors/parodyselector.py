import math
from src.react_utils import (e,
                             createReactClass)
from src import utils
from src.ui import ui
from src.state import state
from src.i18n import tr
from src.single import parodyitem
from src.client import ItemType, ItemSort, client
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')
__pragma__('alias', 'js_input', 'input')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
screen = Object = Date = None
__pragma__('noskip')


def get_db_items(data=None, error=None):
    if data is not None and not error:
        new_data = []
        old_data = this.props.data or this.state.data
        if old_data and len(old_data):
            new_data.extend(old_data)
        new_data.extend(data)
        this.setState({"data": new_data, 'loading': False, 'loading_more': False})
    elif error:
        state.app.notif("Failed to fetch items", level="error")
        this.setState({'loading': False})
    else:
        client.call_func("search_items", this.get_items,
                         item_type=this.state.item_type,
                         search_query=this.state.search_query,
                         sort_by=ItemSort.ParodyName,
                         offset=this.state.limit * (this.state.page - 1),
                         limit=this.state.limit)


def get_items_count(data=None, error=None):
    if data is not None and not error:
        this.setState({"item_count": data['count']})
    elif error:
        state.app.notif("Failed to fetch item count", level="error")
    else:
        client.call_func("get_count", this.get_items_count, item_type=this.state.item_type)


def get_more():
    pages = math.ceil(this.state.item_count / this.state.limit)
    if this.state.page < pages or not this.state.item_count:
        next_page = int(this.state.page) + 1
        this.setState({'page': next_page,
                       'loading_more': True})


def selector_update(p_p, p_s):
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


def selector_on_item_remove(e, d):
    e.preventDefault()
    tid = e.target.dataset.id
    tname = e.target.dataset.js_name
    data = this.state.selected
    if tid and data:
        tid = int(tid)
        ndata = utils.remove_from_list(data, tid, key="id")
        this.setState({'selected': ndata})
    if tname and data:
        ndata = utils.remove_from_list(data, tname, key="preferred_name.name")
        this.setState({'selected': ndata})


def selector_on_item(e, data):
    selected = this.state.selected
    selected_ids = [a.id for a in selected]
    selected_def = this.props.defaultSelected
    selected_def_ids = [a.id for a in selected_def] if selected_def else []
    if data.id in selected_ids:
        selected = utils.remove_from_list(selected, data)
    if data.id in selected_def_ids:
        pass
    else:
        key = 'preferred_name.name'
        selected = utils.update_object(None, this.state.selected, data, op="append",
                                       unique=lambda a, b: a['id'] == b['id'] if a['id'] or b['id'] else utils.get_object_value(key, a) == utils.get_object_value(key, b))
    this.setState({'selected': selected})


def selector_on_new_item(e, d):
    if this.state.search_query:
        active_items = utils.lodash_array.concat(this.state.selected,
                                                 this.props.defaultSelected if this.props.defaultSelected else [])
        new_item = {'preferred_name': {'name': this.state.search_query}}
        old_item = utils.find_in_list(active_items, new_item, key='preferred_name.name')
        if not old_item:
            selected = utils.update_object(None, this.state.selected, new_item, op="append")
            this.setState({'selected': selected, 'search_query': ''})


def selector_on_submit(e, d):
    if this.props.onSubmit:
        this.props.onSubmit(e, this.state.selected)
    if this.props.onClose:
        this.props.onClose()


def selector_render():
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
                     label={'as': 'a',
                            'basic': True,
                            'content': tr(this, "ui.b-new", "New"),
                            'onClick': this.on_new_item} if this.state.search_query else js_undefined,
                     size="mini",
                     value=this.state.search_query,
                     icon='search',
                     fluid=True,
                     onChange=this.update_search),
                   ),
                 ),
               e(ui.Grid.Row,
                 e(ui.Grid.Column,
                   e(ui.Label.Group,
                       [e(parodyitem.ParodyLabel,
                          data=a,
                          key=a.id or utils.get_object_value(
                              'preferred_name.name', a) or utils.get_object_value(
                              'names[0].name', a),
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
            a_els.append(e(parodyitem.ParodyItem,
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
            className="max-400-h min-300-h " + this.props.className if this.props.className else "max-600-h min-500-h",
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


ParodySelector = createReactClass({
    'displayName': 'ParodySelector',

    'getInitialState': lambda: {
        'data': this.props.data or [],
        'selected': [],
        'loading': False,
        'loading_more': False,
        'limit': 20,
        'search_query': this.props.search_query or "",
        'item_count': 0,
        'page': 1,
        'item_type': ItemType.Parody,
        'context_el': None,
    },
    'on_new_item': selector_on_new_item,
    'on_item': selector_on_item,
    'on_item_remove': selector_on_item_remove,
    'on_submit': selector_on_submit,
    'get_items': get_db_items,
    'get_items_count': get_items_count,
    'get_context_el': lambda n: this.setState({'context_el': n}),
    'update_search': lambda e, d: all((this.setState({'search_query': d.value, 'page': 1}),
                                       this.setState({'loading': True}))),
    'get_more': get_more,
    'componentDidMount': lambda: all((this.get_items(), this.get_items_count(), this.setState({'loading': True}))),
    'componentDidUpdate': selector_update,
    'render': selector_render
})
