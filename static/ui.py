__pragma__('alias', 'as_', 'as')
from react_utils import (h,e,
                        render,
                        React,
                        ReactDOM,
                        createReactClass,
                        QueryLink)

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

def Slider(props):
    return e(ui.Segment,
            e(slick,
                *[e(ui.Segment, x, basic=True) for x in props.children],
                dots=True,
                dotsClass="circle slick-dots",
                draggable=True,
                infinite=False,
                centerMode=False,
                accessibility=True,
                lazyLoad=True,
                slidesToShow=4,
                slidesToScroll=2,
                nextArrow=e(SliderNav, direction="right"),
                prevArrow=e(SliderNav, direction="left"),),
                basic=True,
                loading=props.loading)

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

    # check if number is whole
    if pages % 1 == 0:  # Note: will fail on very large numbers eg. 999999999999999999999
        pages = int(pages)
    else:
        pages = int(pages) + 1

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
        items.insert(0, e(ui.Menu.Item, icon="angle left", onClick=go_prev))
    if nav_next:
        items.append(e(ui.Menu.Item, icon="angle right", onClick=go_next))

    return e(ui.Menu,
             *items,
             pagination=True)

Pagination = createReactClass({
    'displayName': 'Pagination',

    'getInitialState': lambda: {'current_page': this.props.default_page if this.props.default_page else 1},

    'change_page': pagination_change,
    'go_page': lambda e, d: this.change_page(int(d.js_name)),
    'go_prev': lambda e, d: this.change_page(this.props.current_page or this.state.current_page - 1),
    'go_next': lambda e, d: this.change_page(this.props.current_page or this.state.current_page + 1),

    'render': pagination_render
})
