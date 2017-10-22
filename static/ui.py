__pragma__('alias', 'as_', 'as')
from react_utils import (h,e,
                        render,
                        React,
                        ReactDOM,
                        createReactClass,
                        QueryLink,
                        ScrollToTop)

from state import state
import math
import utils

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
    items = [e(ui.Segment, x, basic=True, size=props.size, className="slide-segment") for x in children]
    add_el = []
    if props.label:
        add_el.append(e(ui.Label, props.label, e(ui.Label.Detail, len(items)), attached="top"))
    base_size = props.sildesToShow if props.sildesToShow else 5

    if items:
        add_el.append(e(slick,
                    *items,
                    dots=True,
                    dotsClass="circle slick-dots",
                    draggable=True,
                    infinite= False if not utils.defined(props.infinite) else props.infinite,
                    centerMode=False,
                    accessibility=True,
                    lazyLoad=False,
                    adaptiveHeight=True,
                    slidesToShow=base_size,
                    slidesToScroll=base_size-1,
                    nextArrow=e(SliderNav, direction="right"),
                    prevArrow=e(SliderNav, direction="left"),
                    responsive = [
                        { 'breakpoint': 425, 'settings': { 'slidesToShow': base_size-3, 'slidesToScroll': base_size-3 } },
                        { 'breakpoint': 610, 'settings': { 'slidesToShow': base_size-2, 'slidesToScroll': base_size-2 } },
                        { 'breakpoint': 768, 'settings': { 'slidesToShow': base_size-1, 'slidesToScroll': base_size-1 } },
                        { 'breakpoint': 1024, 'settings': { 'slidesToShow': base_size } },
                        { 'breakpoint': 1280, 'settings': { 'slidesToShow': base_size+1 } },
                        { 'breakpoint': 1440, 'settings': { 'slidesToShow': base_size+2 } },
                        { 'breakpoint': 1860, 'settings': { 'slidesToShow': base_size+3 } },
                        { 'breakpoint': 100000, 'settings': 'unslick' } ]))

    return e(ui.Segment,
             *add_el,
                basic=True,
                loading=props.loading,
                secondary=props.secondary,
                tertiary=props.tertiary,
                )
__pragma__("notconv")

def Notif(props):
    return  h("div",
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
    return e(ui.Message, header=props.header,  content=props.content, error=True)

def pagination_change(new_page):
    this.setState({'current_page': new_page})
    if this.props.on_change:
        this.props.on_change(new_page)
    if this.props.scroll_top:
        el = this.props.context or state.container_ref
        if el:
            el.scrollTop = 0

def pagination_render():
    limit = this.props.limit
    if not limit:
        limit = 6
    pages = this.props.pages
    if not pages or pages < 1:
        pages = 1
    current_page = this.props.current_page or this.state.current_page
    if not current_page:
        current_page = 1

    pages = math.floor(pages)

    page_list = range(1, pages + 1)
    ellipsis_pos = 2
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
    l_index = current_page - half_limit
    r_index = current_page + half_limit + 1
    if r_index > len(page_list):
        r_index = len(page_list)
        l_index = len(page_list) - (limit + 1)

    if l_index < 0:
        l_index = 0
        r_index = limit
    current_pages = page_list[l_index:r_index]

    if this.props.query:
        make_items = lambda i: [e(ui.Menu.Item, js_name=str(x), active=current_page==x, onClick=go_page,
                                  as_=QueryLink, query={'page':x}) for x in i]
    else:
        make_items = lambda i: [e(ui.Menu.Item, js_name=str(x), active=current_page==x, onClick=go_page) for x in i]

    items = make_items(current_pages)


    if first_ellipses:
        ellip_items = make_items(page_list[:ellipsis_pos])
        ellip_items.append(e(ui.Menu.Item, "...", disabled=True))
        ellip_items.extend(items)
        items = ellip_items

    if second_ellipses:
        items.append(e(ui.Menu.Item, "...", disabled=True))
        items.extend(make_items(page_list[-ellipsis_pos:]))

    if nav_back:
        if this.props.query:
            items.insert(0, e(ui.Menu.Item, icon="angle left", onClick=go_prev, as_=QueryLink, query={'page':current_page-1}))
        else:
            items.insert(0, e(ui.Menu.Item, icon="angle left", onClick=go_prev))
    if nav_next:
        if this.props.query:
            items.append(e(ui.Menu.Item, icon="angle right", onClick=go_next, as_=QueryLink, query={'page':current_page+1}))
        else:
            items.append(e(ui.Menu.Item, icon="angle right", onClick=go_next))

    return e(ui.Menu,
             *items,
             pagination=True,
             borderless=True,
             size=this.props.size,)

Pagination = createReactClass({
    'displayName': 'Pagination',

    'getInitialState': lambda: {'current_page': this.props.default_page if this.props.default_page else 1},

    'change_page': pagination_change,
    'go_page': lambda e, d: this.change_page(int(d.js_name)),
    'go_prev': lambda e, d: this.change_page((this.props.current_page or this.state.current_page) - 1),
    'go_next': lambda e, d: this.change_page((this.props.current_page or this.state.current_page) + 1),

    'render': pagination_render
})
