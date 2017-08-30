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
    'displayName': 'LibraryPage',

    'getInitialState': lambda: {},

    'render': lambda: e(ui.Grid.Column,
                        e(ui.Container,
                          e(ui.Accordion,
                            e(ui.Accordion.Title,
                              e(ui.Icon, js_name="dropdown"),
                              e(ui.Label,
                                tr(this, "", "View Settings"),
                               as_="a", basic=True)
                              ),
                            e(ui.Accordion.Content,
                              e(ui.Segment)
                              )
                            )
                          ),
                        
                        )
})

