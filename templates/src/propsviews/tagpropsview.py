from src import utils
from src.react_utils import (h,
                             e,
                             Link,
                             createReactClass)
from src.ui import ui
from src.i18n import tr
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

__pragma__("tconv")


def tagprops_render():
    ns = this.props.namespace or this.state.namespace or ""
    tag = this.props.tag or this.state.tag or ""
    if ns == "__namespace__":
        ns = ""
    fav = 0
    description = ""
    if tag:
        description = tr(this, "tag.{}".format(tag), "")

    rows = []

    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, e(ui.Header, e(ui.Header.Subheader, ns), tag, size="medium"), colSpan="2", textAlign="center",
                    verticalAlign="middle")))
    rows.append(e(ui.Table.Row,
                  e(ui.Table.Cell, h("span", description, className="sub-text"), colSpan="2")))
    if ns:
        url_search_query = {'search': '"{}":"{}"'.format(ns, tag)}
    else:
        url_search_query = {'search': '"{}"'.format(tag)}

    # if fav:
    #    lbl_args['icon'] = "star"
    #e(ui.Rating, icon="heart", size="massive", rating=fav)

    return e(ui.Grid,
             e(ui.Grid.Row,
                 e(ui.Grid.Column, e(ui.Rating, icon="heart", size="huge", rating=fav),
                   floated="left", verticalAlign="middle", width=2),
                 e(ui.Grid.Column,
                   e(ui.Button.Group,
                     e(ui.Button, icon="grid layout", title=tr(this, "ui.t-show-galleries", "Show galleries"),
                       as_=Link, to=utils.build_url("/library", query=url_search_query, keep_query=False)),
                     e(ui.Button, icon="heart", title=tr(this, "ui.t-show-fav-galleries", "Show favorite galleries"),
                       as_=Link, to=utils.build_url("/favorite", query=url_search_query, keep_query=False)),
                     basic=True,
                     size="tiny",
                     ),
                   textAlign="right",
                   width=14,
                   verticalAlign="top"),
                 verticalAlign="top",
               ),
             e(ui.Grid.Row,
                 e(ui.Grid.Column,
                   e(ui.Table,
                     e(ui.Table.Body,
                       *rows
                       ),
                     basic="very",
                     size="small",
                     compact="very",
                     ),)),
             )


__pragma__("notconv")

TagProps = createReactClass({
    'displayName': 'TagProps',

    'getInitialState': lambda: {
        'namespace': this.props.namespace,
        'tag': this.props.tag,
        'data': this.props.data,
        'id': this.props.id,
    },

    'render': tagprops_render
})
