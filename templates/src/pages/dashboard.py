from src.react_utils import (e,
                             createReactClass)
from src.ui import ui, Slider
from src.i18n import tr
from src.single import galleryitem
from org.transcrypt.stubs.browser import __pragma__
__pragma__('alias', 'as_', 'as')

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

Page = createReactClass({
    'displayName': 'DasboardPage',

    'componentWillMount': lambda: this.props.menu(None),

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Grid.Column,
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Newest Additions"), attached="top", size="small"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Artist Spotlight"), attached="top", size="small"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Previously Read"), attached="top", size="small"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Based On Today's Tags"), attached="top", size="small"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Because you just read: ") + "XXXXX", attached="top", size="large"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Random"), attached="top", size="large"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "From your favorite artists"), attached="top", size="large"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "From your favorite tags"), attached="top", size="large"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Needs Tagging"), attached="top", size="large"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        e(ui.Segment,
                            e(ui.Label, tr(this, "", "Recently Rated High"), attached="top", size="large"),
                            e(Slider, *[e(galleryitem.Gallery) for x in range(10)]),
                          ),
                        )
})
