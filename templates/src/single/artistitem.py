__pragma__('alias', 'as_', 'as')
import src
from src.react_utils import (h,
                             e,
                             createReactClass)
from src.ui import ui

__pragma__("tconv")
def artistlbl_render():
    name = ""
    fav = 0
    if this.state.data:
        if this.state.data.names:
            name = this.state.data.names[0].js_name
        if this.state.data.metatags.favorite:
            fav = 1


    lbl_args = {'content':name}
    if fav:
        lbl_args['icon'] = "star"
    #e(ui.Rating, icon="heart", size="massive", rating=fav)
    return e(ui.Popup,
                trigger=e(ui.Label,
                    basic=True,
                    as_="a",
                    **lbl_args,
                    ),
                hoverable=True,
                on="click",
                hideOnScroll=True,
                position="top center"
                )
__pragma__("notconv")

ArtistLabel = createReactClass({
    'displayName': 'ArtistLabel',

    'getInitialState': lambda: {'data': this.props.data, 'id':this.props.id},

    'render': artistlbl_render
})