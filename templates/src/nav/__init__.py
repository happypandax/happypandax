class MenuItem:
    __pragma__("kwargs")

    def __init__(self, name, t_id=None,
                 icon="", position="",
                 header=False, handler=None,
                 url=None, modal=None,
                 on_modal_open=None, on_modal_close=None):
        self.name = name
        self.icon = icon
        self.position = position
        self.header = header
        self.children = []
        self.handler = handler
        self.url = url
        self.t_id = t_id
        self.modal = modal
        self.on_modal_open = on_modal_open
        self.on_modal_close = on_modal_close
    __pragma__("nokwargs")

    __pragma__("tconv")

    def has_children(self):
        return bool(self.children)
    __pragma__("notconv")
