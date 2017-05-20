__pragma__ ('alias', 'S', '$') # JQuery

from client import client, Base
import components as cmp
import utils

class IndexPage(Base):
    pass

class ApiPage(Base):

    def call(self):
        func_args = {}
        def each_d(index, element):
            lichildren = S(this).children()
            key = lichildren.eq(0).find("input").val()
            value = lichildren.eq(1).find("input").val()
            if key and value:
                value = value.strip()
                if value.startswith('[') and value.endswith(']'):
                    value = [x.strip() for x in value.replace('[', '').replace(']', '').split(',') if x]
                func_args[key] = value
        S("div#args > ul > li").each(each_d)
        f_dict = {
            'fname': S("#fname").val()
            }
        f_dict.update(func_args)
        client.call(
            [f_dict],
            lambda msg: S("pre#json-receive").html(utils.syntax_highlight(JSON.stringify(msg, None, 4))))
        S("pre#json-send").html(utils.syntax_highlight(JSON.stringify(client._last_msg, None, 4)))

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

api = ApiPage()

class LibraryPage(Base):

    def __init__(self):
        self.grid = None

    def show_items(self, data=None):
        if data:
            items = []
            print(len(data))
            for g in data:
                items.append({
                    'title': g['titles'][0]['name'],
                    'artist': g['artists'][0]['name'],
                    })

            self.compile("items-t", "items", {'items':items})

            self.grid = __new__(Minigrid({
                'container': '.grid-items',
                'item' : '.grid-item',
                'gutter': 10
                }))
            self.grid.mount()
        else:
            client.call_func("library_view", self.show_items,
                             limit=10
                             )


library = LibraryPage()

def init():
    S('div[onload]').trigger('onload')

    window.addEventListener('resize', lambda: library.grid.mount() if library.grid else None)

S(document).ready(init)
