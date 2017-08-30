__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass)
from ui import ui, Slider
from client import client, ServerMsg
from i18n import tr
import utils

Page = createReactClass({
    'displayName': 'DasboardPage',

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Grid.Column,
                        e(ui.Header, tr(this, "", "Newest Additions"), as_="h4"),
                        e(ui.Segment),
                        e(ui.Header, tr(this, "", "Artist Spotlight"), as_="h4"),
                        e(ui.Segment),
                        e(ui.Header, tr(this, "", "Previously Read"), as_="h4"),
                        e(ui.Segment),
                        e(ui.Header, tr(this, "", "Based On Today's Tags"), as_="h4"),
                        e(ui.Segment),
                        e(ui.Header, tr(this, "", "Random"), as_="h4"),
                        e(ui.Segment),
                        e(ui.Header, tr(this, "", "Needs Tagging"), as_="h4"),
                        e(ui.Segment),
                        e(ui.Header, tr(this, "", "Recently Rated High"), as_="h4"),
                        e(ui.Segment),
                        )
})

