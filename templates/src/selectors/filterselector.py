import math
from src.react_utils import (e,
                             createReactClass)
from src import utils
from src.ui import ui
from src.state import state
from src.single import GenericItem
from src.client import ItemType, client
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

__pragma__('kwargs')


def add_item(data=None, error=None, new_data=None):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to add to filter ({})".format(this.state.id), level="error")
    else:
        new_data = new_data or this.state.new_data
        print("add")
        client.call_func("add_to_filter", this.add_item,
                         gallery_id=this.props.item_id,
                         item=new_data)


__pragma__('nokwargs')

__pragma__('kwargs')


def remove_item(data=None, error=None, new_data=None):
    if data is not None and not error:
        pass
    elif error:
        state.app.notif("Failed to remove from filter ({})".format(this.state.id), level="error")
    else:
        new_data = new_data or this.state.new_data
        if new_data.id:
            client.call_func("remove_from_filter", this.remove_item,
                             gallery_id=this.props.item_id,
                             item_id=new_data.id)


__pragma__('nokwargs')


def get_current_db_items(data=None, error=None):
    if data is not None and not error:
        this.setState({"default_selected": data})
    elif error:
        state.app.notif("Failed to fetch current items", level="error")
    else:
        client.call_func("get_related_items", this.get_current_items,
                         item_id=this.props.item_id,
                         item_type=this.props.item_type,
                         related_type=this.state.item_type,
                         limit=9999)


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
        client.call_func("get_items", this.get_items,
                         item_type=this.state.item_type,
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


def selector_on_item(e, data):
    selected = this.state.selected
    selected_ids = [a.id for a in selected]
    selected_def = this.state.default_selected
    selected_ids_def = [a.id for a in selected_def]
    if data.id in selected_ids or data.id in selected_ids_def:
        selected_def = utils.remove_from_list(selected_def, data)
        selected = utils.remove_from_list(selected, data)
        if this.props.item_id:
            this.remove_item(new_data=data)
    else:
        selected = utils.JSONCopy(selected)
        selected.append(data)
        if this.props.item_id:
            this.add_item(new_data=data)

    this.setState({'selected': selected, 'default_selected': selected_def})


def selector_on_submit(e, d):
    if this.props.onSubmit:
        this.props.onSubmit(e, this.state.selected)
    if this.props.onClose:
        this.props.onClose()


def selector_render():
    data = this.props.data or this.state.data
    selected = this.state.selected

    selected_ids = [a.id for a in selected]
    if this.state.default_selected:
        default_selected = this.state.default_selected
        selected_ids.extend([a.id for a in default_selected])
    a_els = []
    if data:
        for a in sorted(data, key=lambda a: a.js_name):
            a_els.append(e(GenericItem,
                           data=a,
                           active=a.id in selected_ids,
                           key=a.id,
                           selection=True,
                           onClick=this.on_item,
                           icon=e(ui.Icon, js_name="filter"),
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
            className="max-400-h min-200-h " + this.props.className if this.props.className else "max-600-h min-500-h",
            verticalAlign="middle")

    return e(ui.Segment,
             e(ui.Ref,
               els,
               innerRef=this.get_context_el,
               ),
             basic=True,
             loading=this.state.loading,
             )


FilterSelector = createReactClass({
    'displayName': 'FilterSelector',

    'getInitialState': lambda: {
        'data': this.props.data or [],
        'selected': [],
        'loading': False,
        'loading_more': False,
        'limit': 99999,
        'item_count': 0,
        'page': 1,
        'default_selected': this.props.defaultSelected or [],
        'item_type': ItemType.GalleryFilter,
        'context_el': None,
    },
    'on_item': selector_on_item,
    'on_submit': selector_on_submit,
    'get_current_items': get_current_db_items,
    'add_item': add_item,
    'remove_item': remove_item,
    'get_items': get_db_items,
    'get_items_count': get_items_count,
    'get_context_el': lambda n: this.setState({'context_el': n}),
    'update_search': lambda e, d: all((this.setState({'search_query': d.value, 'page': 1}),
                                       this.setState({'loading': True}))),
    'get_more': get_more,
    'componentDidMount': lambda: all((this.get_items(),
                                      this.get_items_count(),
                                      this.get_current_items() if this.props.item_type and this.props.item_id else None,
                                      this.setState({'loading': True}))),
    'componentDidUpdate': selector_update,
    'render': selector_render
})
