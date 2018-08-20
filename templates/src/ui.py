import math
from src.react_utils import (h, e,
                             React,
                             createReactClass,
                             QueryLink)

from src.state import state
from src.i18n import tr
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

ui = require("semantic-ui-react")

slick = require('react-slick')['default']
Alert = require('react-s-alert')['default']


def SliderNav(props):
    return e(ui.Icon,
             js_name="chevron {}".format(props.direction),
             link=True,
             circular=True,
             inverted=True,
             className="slide-next {}".format(props.direction),
             onClick=props.onClick)


__pragma__("tconv")


def Slider(props):
    children = props.data or React.Children.toArray(props.children)
    items = [e(ui.Segment, x,
               basic=True, size=props.size, className="slide-segment") for x in children]
    add_el = []
    if props.label:
        add_el.append(e(ui.Label, props.label, e(ui.Label.Detail, len(items)), color=props.color, attached="top"))
    base_size = props.sildesToShow if props.sildesToShow else 5

    if items:
        add_el.append(e(slick,
                        *items,
                        dots=True,
                        dotsClass="slick-dots",
                        draggable=True,
                        variableWidth=True,
                        infinite=False if not utils.defined(props.infinite) else props.infinite,
                        centerMode=False,
                        accessibility=True,
                        lazyLoad=False,
                        adaptiveHeight=props.adaptiveHeight if utils.defined(props.adaptiveHeight) else False,
                        slidesToShow=base_size,
                        slidesToScroll=base_size - 1,
                        nextArrow=e(SliderNav, direction="right"),
                        prevArrow=e(SliderNav, direction="left"),
                        responsive=[
                            {'breakpoint': 425, 'settings': {'slidesToShow': base_size - 3, 'slidesToScroll': base_size - 3}},
                            {'breakpoint': 610, 'settings': {'slidesToShow': base_size - 2, 'slidesToScroll': base_size - 2}},
                            {'breakpoint': 768, 'settings': {'slidesToShow': base_size - 1, 'slidesToScroll': base_size - 1}},
                            {'breakpoint': 1024, 'settings': {'slidesToShow': base_size}},
                            {'breakpoint': 1280, 'settings': {'slidesToShow': base_size + 1}},
                            {'breakpoint': 1440, 'settings': {'slidesToShow': base_size + 2}},
                            {'breakpoint': 1860, 'settings': {'slidesToShow': base_size + 3}},
                            {'breakpoint': 100000, 'settings': {'slidesToShow': base_size + 3}},
                        ]))

    return e(ui.Segment,
             *add_el,
             basic=props.basic if utils.defined(props.basic) else True,
             loading=props.loading,
             secondary=props.secondary,
             tertiary=props.tertiary,
             className="no-padding-segment"
             )


__pragma__("notconv")


def Notif(props):
    return h("div",
             h("div",
               e(ui.Message,
                 header=props.customFields.header,
                 content=props.customFields.content,
                 onDismiss=props.handleClose,
                 **props.customFields.mskwargs,),
               className="s-alert-box-inner",),
             className=props.classNames,
             id=props.id,
             style=props.styles,)


def Error(props):
    return e(ui.Message, header=props.header, content=props.content, error=True)


__pragma__("kwargs")


def pagination_change(new_page, no_scroll=False):
    this.setState({'current_page': new_page})
    if this.props.on_change:
        this.props.on_change(new_page)
    if this.props.scroll_top and this.props.query and not no_scroll:
        el = this.props.context or state.container_ref
        utils.scroll_to_element(el)


__pragma__("nokwargs")


def pagination_receive_props(n_props):
    n_page = int(utils.get_query("page", this.state.current_page))
    if this.props.query and\
            n_props.location != this.props.location and\
            n_page != this.state.current_page and \
            n_page != this.props.current_page:
        this.change_page(n_page)


def pagination_render():
    limit = this.props.limit
    if not limit:
        limit = 6
    pages = this.props.pages
    if not pages or pages < 1:
        pages = 1
    current_page = this.props.current_page or this.state.current_page
    if this.props.history and this.props.query and not current_page:
        current_page = utils.get_query("page", this.state.current_page)
    if not current_page:
        current_page = 1
    current_page = int(current_page)

    pages = math.ceil(pages)

    page_list = range(1, pages + 1)
    ellipsis_pos = 2 if limit > 2 else 1
    nav_back = True
    nav_next = True
    first_ellipses = False
    second_ellipses = False

    if current_page - 1 == 0:
        nav_back = False

    if current_page == len(page_list):
        nav_next = False

    if limit and current_page > limit and current_page > ellipsis_pos:
        first_ellipses = True

    if (pages - current_page) > limit and pages > ellipsis_pos:
        second_ellipses = True

    go_next = this.go_next
    go_prev = this.go_prev
    go_page = this.go_page

    half_limit = int(limit / 2)
    l_index = current_page - (half_limit if half_limit else 1)
    r_index = current_page + half_limit + 1
    if r_index > len(page_list):
        r_index = len(page_list)
        l_index = len(page_list) - (limit + 1)

    if l_index < 0:
        l_index = 0
        r_index = limit
    current_pages = page_list[l_index:r_index]

    if this.props.query:
        def make_items(i): return [e(ui.Menu.Item, js_name=str(x), active=current_page == x, onClick=go_page,  # noqa: E704
                                     as_=QueryLink, query={'page': x}) for x in i]  # noqa: E704
    else:
        def make_items(i): return [e(ui.Menu.Item, js_name=str(  # noqa: E704
            x), active=current_page == x, onClick=go_page) for x in i]  # noqa: E704

    items = make_items(current_pages)

    query_args = {}
    if this.props.query:
        query_args = {'as': QueryLink, 'query': {'page': this.state.go_to_page}}
    go_el = e(ui.Popup,
              e(ui.Form,
                  e(ui.Form.Field,
                    e(ui.Input,
                      onChange=this.go_to_change,
                      size="mini",
                      js_type="number",
                      placeholder=current_page,
                      action=e(ui.Button, js_type="submit", compact=True, icon="share", onClick=this.go_to_page,
                               **query_args),
                      min=0, max=pages),
                    ),
                  onSubmit=this.go_to_page
                ),
              on="click",
              hoverable=True,
              position="top center",
              trigger=e(ui.Menu.Item, "..."))

    if first_ellipses:
        ellip_items = make_items(page_list[:ellipsis_pos])
        ellip_items.append(go_el)
        ellip_items.extend(items)
        items = ellip_items

    if second_ellipses:
        items.append(go_el)
        items.extend(make_items(page_list[-ellipsis_pos:]))

    if nav_back:
        if this.props.query:
            items.insert(0, e(ui.Menu.Item, icon="angle left", onClick=go_prev,
                              as_=QueryLink, query={'page': current_page - 1}))
        else:
            items.insert(0, e(ui.Menu.Item, icon="angle left", onClick=go_prev))
    if nav_next:
        if this.props.query:
            items.append(e(ui.Menu.Item, icon="angle right", onClick=go_next,
                           as_=QueryLink, query={'page': current_page + 1}))
        else:
            items.append(e(ui.Menu.Item, icon="angle right", onClick=go_next))

    return e(ui.Menu,
             *items,
             pagination=True,
             borderless=True,
             size=this.props.size if utils.defined(this.props.size) else "small",
             as_=ui.Transition.Group,
             duration=1000,
             )


Pagination = createReactClass({
    'displayName': 'Pagination',

    'getInitialState': lambda: {
        'current_page': this.props.default_page if this.props.default_page else
        (utils.get_query("page", 1) if this.props.history and this.props.query else 1),
        'go_to_page': 1,
    },

    'change_page': pagination_change,
    'go_to_change': lambda e, d: this.setState({'go_to_page': int(d.value)}),
    'go_to_page': lambda e, d: this.change_page(int(this.state.go_to_page)),
    'go_page': lambda e, d: this.change_page(int(d.js_name)),
    'go_prev': lambda e, d: this.change_page((int(this.props.current_page or this.state.current_page) - 1)),
    'go_next': lambda e, d: this.change_page(int(this.props.current_page or this.state.current_page) + 1),

    'componentDidMount': lambda: this.change_page(this.props.current_page or this.props.default_page or utils.get_query("page", 1), True) if this.props.history and this.props.query else None,
    'componentWillReceiveProps': pagination_receive_props,

    'render': pagination_render
})


ToggleIcon = createReactClass({
    'displayName': 'ToggleIcon',

    'getInitialState': lambda: {'toggled': this.props.toggled},

    'toggle': lambda: all((this.setState({'toggled': not this.state.toggled}),
                           this.props.on_toggle(not this.state.toggled) if this.props.on_toggle else None)),

    'render': lambda: e(ui.Icon,
                        this.props.children,
                        js_name=this.props.icons[int(this.state.toggled) if this.props.icons else ""],
                        onClick=this.toggle,
                        link=True,
                        )
}, pure=True)


def connectstatus_render():
    return e(ui.Sticky,
             e(ui.Icon, js_name="circle notched",
               loading=True, size="big", color="grey",
               circular=True, style={'float': "right", 'marginRight': "35px"}),
             offset=55,
             context=this.props.context,
             className="foreground-sticky")


ConnectStatus = createReactClass({
    'displayName': 'ConnectStatus',

    'getInitialState': lambda: {'connected': False},

    'toggle': lambda: all((this.setState({'toggled': not this.state.toggled}),
                           this.props.on_toggle(not this.state.toggled) if this.props.on_toggle else None)),

    'render': connectstatus_render,
}, pure=True)

LabelAccordion = createReactClass({
    'displayName': 'LabelAccordion',

    'getInitialState': lambda: {'open': (utils.storage.get('labelaccordion' + this.props.cfg_suffix, this.props.default_open) if this.props.cfg_suffix else this.props.default_open) or False
                                },

    'toggle': lambda: all((this.setState({'open': not this.state.open}),
                           this.props.on_toggle(not this.state.open) if this.props.on_toggle else None),
                          utils.storage.set('labelaccordion' + this.props.cfg_suffix, not this.state.open) if this.props.cfg_suffix else None),

    'render': lambda: e(ui.Segment,
                        e(ui.Label,
                          e(ui.Icon, js_name="caret down" if this.state.open else "caret right"),
                          this.props.label,
                          *([e(ui.Label.Detail, this.props.detail)] if utils.defined(this.props.detail) else []),
                          attached=this.props.attached or "top",
                          onClick=this.toggle,
                          color=this.props.color,
                          as_="a",
                          ),
                        this.props.children if this.state.open else js_undefined,
                        compact=this.props.compact,
                        secondary=this.props.secondary,
                        basic=this.props.basic if utils.defined(this.props.basic) else True,
                        className="small-padding-segment",
                        ),
}, pure=True)


def TitleChange(props):
    document.title = props.title + ' - ' + state.title if props.title else state.title
    return None


def tr_render():
    return tr(this, this.props.children, this.props.default)


TR = createReactClass({
    'displayName': 'TR',


    'render': tr_render,
}, pure=True)


# def onhover_render():
#    return h(this.props.as_ or "div", this.props.children,
#             onMouseEnter=this.on_mouse_over,
#             onMouseLeave=this.on_mouse_over,
#             onClick=this.props.onClick,
#             )


# OnHover = createReactClass({
#    'displayName': 'OnHover',
#    'getInitialState': lambda: {'hover': False},
#    'on_mouse_over': lambda e,d: all((this.setState({'hover': not this.state.hover}),
#                                  this.props.onHover() if this.props.onHover and (not this.state.hover) else None)),

#    'render': onhover_render,
# }, pure=True)

def RemovableItem(props):
    return e(ui.Message,
             props.children,
             as_=ui.Segment,
             basic="very",
             onDismiss=props.onRemove if props.onRemove else lambda: None,
             color=props.color)
