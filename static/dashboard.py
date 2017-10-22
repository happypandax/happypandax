__pragma__('alias', 'as_', 'as')
from react_utils import (h,
                         e,
                         React,
                         createReactClass)
from ui import ui, Slider
from client import client, ServerMsg
from i18n import tr
from state import state
import utils
import items

Page = createReactClass({
    'displayName': 'DasboardPage',

    'componentWillMount': lambda: this.props.menu(None),

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Grid.Column,
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Newest Additions"), attached="top", size="small"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Artist Spotlight"), attached="top", size="small"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Previously Read"), attached="top", size="small"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Based On Today's Tags"), attached="top", size="small"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                         e(ui.Segment,
                            e(ui.Label, tr(this, "", "Because you just read: ") + "XXXXX", attached="top", size="large"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Random"), attached="top", size="large"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "From your favorite artists"), attached="top", size="large"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                            ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "From your favorite tags"), attached="top", size="large"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                            ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Needs Tagging"), attached="top", size="large"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Recently Rated High"), attached="top", size="large"),
                            e(Slider,*[e(items.Gallery) for x in range(10)]),
                          ),
                        )
})

