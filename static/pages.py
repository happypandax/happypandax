__pragma__('alias', 'S', '$')  # JQuery

from client import client, Base, ServerMsg
import utils
import widget


class BasePage(Base):

    def main(self):
        moment.locale(utils.get_locale())

    def config_save(name):
        pass

    def config_get(name):
        pass


class ApiPage(Base):

    def __init__(self, url="/apiview"):
        super().__init__(url)

    @classmethod
    def get_type(cls, s):

        if s[0] in ("'", '"') and s[len(s) - 1] in ("'", '"'):
            return s[1:-1]
        elif s.lower() in ('none', 'null'):
            return None
        else:
            try:
                return int(s)
            except ValueError:
                return s

    def call(self):
        func_args = {}

        def each_d(index, element):
            lichildren = S(this).children()
            key = lichildren.eq(0).find("input").val()
            value = lichildren.eq(1).find("input").val()
            if key and value:
                value = value.strip()
                if value.startswith('[') and value.endswith(']'):
                    value = [
                        self.get_type(x.strip()) for x in value.replace(
                            '[', '').replace(
                            ']', '').split(',') if x]

                if isinstance(value, str):
                    value = self.get_type(value)

                func_args[key] = value

        S("div#args > ul > li").each(each_d)

        f_dict = {
            'fname': S("#fname").val()
        }

        f_dict.update(func_args)

        client.call(ServerMsg([f_dict], lambda msg: S(
            "pre#json-receive").html(utils.syntax_highlight(JSON.stringify(msg, None, 4)))))

        S("pre#json-send").html(utils.syntax_highlight(JSON.stringify(client._last_msg['msg'], None, 4)))

    def add_kwarg(self):
        S("div#args > ul").append(
            """
            <li>
            <div class='col-xs-6'>
            <input type='text', placeholder='keyword' class='form-control'>
            </div>
            <div class='col-xs-6'>
            <input type='text', placeholder='value' class='form-control'>
            </div>
            </li>
            """)


class LibraryPage(Base):

    def __init__(self, name="Library", url="/library"):
        super().__init__(url)
        self.name = name
        self.items = {}  # id : item obj
        self.artists = {}  # id : item obj
        self.tags = {}  # ns : tag
        self.gfilters = {}  # id : item obj
        self.item_limit = 100
        self._page_limit = 10
        self._page_list = []
        self.current_page = 1

        self._properties = {
            'search_query': '',
            'view': 'Gallery',
            'sort': 'Title',
            'sort_order': 'Ascending',
            'group': False,
            'iscroll': False
        }

        self.grid = utils.Grid("#items", "#items .gallery", gutter=20)

    def context_nav(self, *args):
        """
        Insert a breadcumb element
        Pass tuples of (name, url)
        """

        ctx_links = [{'name': x[0], 'url': x[1]} for x in args]

        self.compile(
            "#context-nav-t",
            "#item-main",
            prepend=True,
            context_links=ctx_links)

    def update_context(self):
        return
        self.context_nav(*self._context_link)

    def add_context(self, name, url):
        self._context_link.append((name, url))
        self.update_context()

    def reset_context(self):
        self._context_link = [(self.name, self.url)]

    def set_properties(self):
        ""
        S("#current-view").text(self._properties['view'])

    def get_property(self, p):
        r = self._properties[p]
        if p == 'view' and self._properties['group'] and r == 'Gallery':
            r = 'Grouping'
        return r

    def main(self):
        super().main()
        self.fetch_gfilters()
        self.show_pagination()

    __pragma__('iconv')
    __pragma__('kwargs')

    def update_sidebar(self, lists=None, tags=None, artist_obj={}):
        ""
        if artist_obj is not None:
            artist_data = []
            for a in artist_obj:
                artist_data.append(
                    {'name': artist_obj[a]['name'], 'count': artist_obj[a]['count']})
            self.compile(
                "#side-artists-t",
                "#side-artists",
                side_artists=artist_data)
    __pragma__('nokwargs')
    __pragma__('noiconv')

    def update_pagination(self, from_page=1):
        ""
        self.current_page = from_page

        back_disabled = False
        next_disabled = False

        if from_page - 1 == 0:
            back_disabled = True

        if from_page == len(self._page_list):
            next_disabled = True

        half_limit = int(self._page_limit / 2)
        l_index = from_page - half_limit
        r_index = from_page + half_limit + 1
        if r_index > len(self._page_list):
            r_index = len(self._page_list)
            l_index = len(self._page_list) - (self._page_limit + 1)

        if l_index < 0:
            l_index = 0
            r_index = self._page_limit
        current_pages = self._page_list[l_index:r_index]

        pages = []

        for n in current_pages:
            pages.append({'number': n, 'active': n == from_page})

        self.show_items(page=from_page)

        self.compile("#item-pagination-t", ".item-pagination",
                     pages=pages,
                     back_button=not back_disabled,
                     next_button=not next_disabled,
                     back_number=from_page - 1,
                     next_number=from_page + 1)

    def show_pagination(self, data=None, error=None):
        ""
        if data is not None and not error:
            pages = data['count'] / self.item_limit
            if pages < 1:
                pages = 1
            # check if number is whole
            if pages % 1 == 0:  # Note: will fail on very large numbers eg. 999999999999999999999
                pages = int(pages)
            else:
                pages = int(pages) + 1
            self._page_list = range(1, pages + 1)
            self.update_pagination()
        elif error:
            pass
        else:
            client.call_func(
                "get_view_count",
                self.show_pagination,
                item_type=self.get_property('view'),
                search_query=self.get_property('search_query'))

    def fetch_gfilters(self, data=None, error=None):
        ""
        if data is not None and not error:
            lists_data = []
            for gl in data:
                self.gfilters[gl['id']] = gl
                lists_data.append({'name': gl['name']})

            self.compile(
                "#side-lists-t",
                "#side-lists .list-group",
                append=True,
                side_lists=lists_data)
        elif error:
            pass
        else:
            client.call_func("get_items", self.fetch_gfilters, item_type='galleryfilter')

    __pragma__('iconv')
    __pragma__('tconv')
    __pragma__('kwargs')

    def show_items(self, data=None, error=None, page=None):
        if not page:
            page = self.current_page

        if data is not None and not error:
            self.set_properties()
            self.artists.clear()
            _view = self.get_property('view')
            items = []
            if _view == 'Gallery':
                if not self._properties['iscroll']:
                    self.items.clear()
                    S("#items").empty()
                for g in data:
                    g_obj = widget.Gallery('medium', g)
                    self.items[g['id']] = g_obj

                    items.append(g_obj)

                    for a in g['artists']:
                        a_id = a['id']
                        if a_id in self.artists:
                            self.artists[a_id]['count'] += 1
                        else:
                            self.artists[a_id] = a
                            self.artists[a_id]['count'] = 1

            self.update_sidebar(artist_obj=self.artists)
            if items:
                for i in items:
                    i.compile("#items", append=True)
                    i.fetch_thumb()

            if not items:
                self.show_nothing("#items")

            self.grid.reload()
            self.grid.layout()

        elif error:
            pass
        else:
            view = self.get_property('view')

            client.call_func("library_view", self.show_items,
                             item_type=view,
                             limit=self.item_limit,
                             page=page - 1,
                             search_query=self._properties['search_query']
                             )
    __pragma__('noiconv')
    __pragma__('notconv')
    __pragma__('nokwargs')

    def set_property(self, p, v):
        self._properties[p] = v
        self.show_pagination()

    def update_search_query(self):
        sq = S("#search").val()
        self.log("search query: {}".format(sq))
        self._properties['search_query'] = sq
        self.show_pagination()

    def show_nothing(self, target_el):
        ""
        self.compile("#nothing-t", target_el)


class InboxPage(BasePage):

    def __init__(self, name="Inbox", url="/inbox"):
        super().__init__(name, url)


class FavortiesPage(BasePage):

    def __init__(self, name="Favorites", url="/fav"):
        super().__init__(name, url)


class GalleryPage(Base):
    def __init__(self):
        super().__init__()
        self.obj = None
        self.g_id = self.url.path().split('/')[2]

    def main(self):
        super().main()
        self.show_gallery()

    def show_gallery(self, data=None, error=None):
        ""
        if data is not None and not error:
            self.obj = widget.Gallery('page', data)
            self.compile("#gallery-t",
                         ".breadcrumb", after=True,
                         thumb="/static/img/default.png",
                         title=self.obj.title(),
                         artists=data['artists'],
                         lang="test",
                         inbox=data["inbox"],
                         fav=data["fav"],
                         published=moment.unix(data['pub_date']).format("LL"),
                         updated=moment.unix(data['last_updated']).format("LLL"),
                         read=moment.unix(data['last_read']).format("LLL"),
                         added=moment.unix(data['timestamp']).format("LLL"),
                         rel_added=moment.unix(data['timestamp']).fromNow(),
                         rel_updated=moment.unix(data['last_updated']).fromNow(),
                         rel_read=moment.unix(data['last_read']).fromNow())
            widget.Thumbnail("#profile", "big", "Gallery", self.obj['id']).fetch_thumb()
        elif error:
            pass
        else:
            client.call_func("get_item", self.show_gallery, item_type='Gallery', item_id=int(self.g_id))

_pages = {}

__pragma__('kwargs')


def init_page(p, cls, *args, **kwargs):
    _pages[p] = cls(*args, **kwargs)
    return _pages[p]
__pragma__('nokwargs')


def get_page(p):
    return _pages[p]


def init():
    S('div[onload]').trigger('onload')

S(document).ready(init)
