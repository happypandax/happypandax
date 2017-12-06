__pragma__('alias', 'as_', 'as')
import src
from src import utils
from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui
from src.i18n import tr
from src.client import ItemType, client
from src.single import tagitem

def get_tags(data=None, error=None):
    if data is not None and not error:
        this.setState({"tags": data})
    elif error:
        state.app.notif("Failed to fetch tags ({})".format(this.props.id), level="error")
    else:
        id = this.state.id
        if this.state.data:
            id = this.state.data.id
        client.call_func("get_common_tags", this.get_tags,
                         item_type=this.state.item_type,
                         item_id=id, limit=10)

__pragma__("tconv")
def artistlbl_render():
    name = ""
    fav = 0
    nstags = this.state.tags or {}
    if this.state.data:
        if this.state.data.names:
            name = this.state.data.names[0].js_name
        if this.state.data.metatags.favorite:
            fav = 1

    tag_lbl = []

    if nstags.__namespace__:  # somehow transcrypt ignores this in the loop below
        tags = sorted([x.js_name for x in nstags.__namespace__])
        for t in tags:
            tag_lbl.append(e(tagitem.TagLabel, tag=t))

    for ns in sorted(dict(nstags).keys()):
        tags = sorted([x.js_name for x in nstags[ns]])
        for t in tags:
            tag_lbl.append(e(tagitem.TagLabel, namespace=ns, tag=t, show_ns=True))


    lbl_args = {'content':name}
    if fav:
        lbl_args['icon'] = "star"
    return e(ui.Popup,
             e(ui.Grid,
               e(ui.Grid.Row, e(ui.Grid.Column, e(ui.Rating, icon="heart", size="huge", rating=fav))),
               e(ui.Grid.Row, e(ui.Grid.Column,
                                e(ui.Segment,
                                 e(ui.Label, tr(this, "", "Most common tags"), attached="top"),
                                 e(ui.Label.Group,
                                   *tag_lbl
                                   ),
                                 basic=True,
                                 ),
                                width=16), columns=1),
               ),
                trigger=e(ui.Label,
                    basic=True,
                    as_="a",
                    **lbl_args,
                    ),
                hoverable=True,
                wide="very",
                on="click",
                hideOnScroll=True,
                position="top center"
                )
__pragma__("notconv")

ArtistLabel = createReactClass({
    'displayName': 'ArtistLabel',

    'getInitialState': lambda: {
        'id':this.props.id,
        'data': this.props.data, 
        'tags': this.props.tags,
        'item_type': ItemType.Artist,
        },

    'get_tags': get_tags,

    'componentDidMount': lambda: this.get_tags() if not utils.defined(this.props.tags) else None,

    'render': artistlbl_render
})