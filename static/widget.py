__pragma__('alias', 'S', '$')  # JQuery

from client import client, thumbclient, Base, Command


class Widget(Base):

    def __init__(self, source_el):
        super().__init__()
        self._source_el = source_el
        self.node = None

    __pragma__('kwargs')

    def compile(
            self,
            target_el,
            after=None,
            before=None,
            append=None,
            prepend=None,
            **data):
        """
        Compile widget into target element
        Set after, before, append or prepend to True to specify where to insert html.
        """
        self.node = super().compile(self._source_el, target_el,
                                    after=after, before=before,
                                    append=append, prepend=prepend,
                                    **data)

    __pragma__('nokwargs')

    def get_node(self):

        if not self.node:
            self.node = S(self._source_el)

        return self.node


class Thumbnail(Widget):

    def __init__(self, source_el, size_type, item_type, id):
        super().__init__(source_el)
        self.thumbclient = thumbclient
        self.item_type = item_type
        self.size_type = size_type
        self.id = id
        self._thumbs = {
            'Big': None,
            'Medium': None,
            'Small': None
        }
        self._thumbsize = None

    __pragma__('tconv')
    __pragma__('kwargs')

    def _fetch_thumb(self, data=None, error=None, size='Big'):
        if data is not None and not error:
            cmd_id = data[str(self.id)]
            cmd = Command(cmd_id)
            self._thumbs[self._thumbsize] = cmd
            cmd.set_callback(self._set_thumb_cmd)
            cmd.poll_until_complete(500)
        elif error:
            pass
        else:
            print("getting")
            if self.id is not None:
                self._thumbsize = size
                self.thumbclient.call_func("get_image", self._fetch_thumb, item_ids=[self.id],
                                 size=size, local=False, uri=True, item_type=self.item_type)
    __pragma__('notconv')
    __pragma__('nokwargs')

    __pragma__('tconv')

    def _set_thumb_cmd(self, cmd):
        val = cmd.get_value()
        im = None
        if val:
            im = val['data']

        self._thumbs[self._thumbsize] = val

        if not im:
            im = "/static/img/no-image.png"

        self._set_thumb(im)
    __pragma__('notconv')

    def _set_thumb(self, im):
        if self.get_node() and im:
            self.node.find('img').attr('src', im)
            self.node.find('.load').fadeOut(300)

    __pragma__('tconv')

    def fetch_thumb(self):
        if not self.size_type:
            return

        s = {
            'big': 'Big',
            'medium': 'Medium',
            'small': 'Small'
        }

        size = s[self.size_type]
        if self._thumbs[size]:
            self._set_thumb(self._thumbs[size])
        else:
            self._fetch_thumb(size=size)
    __pragma__('notconv')


class Gallery(Thumbnail):

    __pragma__('kwargs')

    def __init__(self, gtype='medium', gallery_obj={}):
        self.obj = gallery_obj
        id = None
        if 'id' in self.obj:
            id = self.obj['id']
        super().__init__("#gallery-" + gtype + "-t", gtype, 'Gallery', id)
        self._gtype = gtype
    __pragma__('nokwargs')

    __pragma__('tconv')

    def title(self):
        "Returns title in preffered language"
        t = ""

        if self.obj:
            if self.obj['titles']:
                t = self.obj['titles'][0]['name']

        return t
    __pragma__('notconv')

    def titles(self):
        "Returns all titles"
        pass

        return a

    def get(self):
        g = {}
        g['id'] = self.obj['id']

        if self._gtype == 'medium':
            g['title'] = self.title()
            g['thumb'] = "static/img/default.png"
        return g

    __pragma__('kwargs')

    def compile(
            self,
            target_el,
            after=None,
            before=None,
            append=None,
            prepend=None):
        """
        Compile widget into target element
        Set after, before, append or prepend to True to specify where to insert html.
        """
        return super().compile(target_el,
                               after=after, before=before,
                               append=append, prepend=prepend,
                               **self.get())

    __pragma__('nokwargs')
