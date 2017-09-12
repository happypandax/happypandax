__pragma__('alias', 'as_', 'as')
from react_utils import (h,e,
                        render,
                        React,
                        ReactDOM,
                        createReactClass)

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

def pagination_render():
    limit = this.props.limit
    if not limit:
        limit = 10
    pages = this.props.pages
    if not pages:
        pages = 0
    current_page = this.state.current_page
    if not current_page:
        current_page = 0

    ellipsis_pos = 3
    nav_buttons = False
    first_ellipses = False
    second_ellipses = False

    if limit and current_page > limit and current_page > ellipsis_pos:
        first_ellipses = True

    if (pages - current_page) > limit and pages > ellipsis_pos:
        second_ellipses = True

    setState = this.setState
    items = []
    if pages:
        pass

    if not first_ellipses and not second_ellipses:
        items = [e(ui.Menu.Item, js_name=str(x), active=current_page==x, onClick=lambda e, n: setState({'current_page':int(n)})) for x in range(limit)]

    if len(items) > 1:
        nav_buttons = True


    if nav_buttons:
        items.insert(0, e(ui.Menu.Item, icon="angle left", onClick=this.prev))
        items.append(e(ui.Menu.Item, icon="angle right", onClick=this.next))

    if first_ellipses:
        items.insert(ellipsis_pos-1, e(ui.Menu.Item, js_name="...", disabled=True))

    if second_ellipses:
        items.insert(limit-ellipsis_pos, e(ui.Menu.Item, js_name="...", disabled=True))

    return e(ui.Menu,
             *items,
             pagination=True)

Pagination = createReactClass({
    'displayName': 'Pagination',

    'getInitialState': lambda: {'current_page': this.props.current_page},

    'prev': lambda:1,
    'next': lambda:1,

    'render': pagination_render
})
