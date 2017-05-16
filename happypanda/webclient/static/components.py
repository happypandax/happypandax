__pragma__ ('alias', 'S', '$') # JQuery

from client import client, Base

class Component(Base):
    
    def __init__(self, c_id=None):
        self._id = c_id

    def append(self, el):
        "Append component to the end of element contents"
        S(el).append(self.html())

    def prepend(self, el):
        "Preprend component to the beginning of element contents"
        S(el).preprend(self.html())

    def remove(self, el=None):
        "Remove component from all elements or specified element"
        if el:
            S(el).remove(self._id)
        else:
            S(self._id).remove()

    def html(self):
        raise NotImplementedError


class Gallery(Component):

    def __init__(self, g_dict):
        super().__init__('gallery_' + g_dict['id'])
        self._dict = g_dict

    def html(self):
        h = ""
        return super().html()