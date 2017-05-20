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
                func_args[key] = value
        S("div#args > ul > li").each(each_d)
        client.call_function(
            S("#fname").val(),
            lambda msg: S("pre#json-receive").html(utils.syntax_highlight(JSON.stringify(msg, None, 4))),
            **func_args)
        S("pre#json-send").html(utils.syntax_highlight(JSON.stringify(client._last_msg, None, 4)))

    def add_kwarg(self):
        S("div#args > ul").append("<li><span><input type='text', placeholder='keyword'></span><span><input type='text', placeholder='value'></span></li>")

api = ApiPage()

class LibraryPage(Base):

    def __init__(self):
        super().__init__()

    def show_galleries(self):
        pass


library = LibraryPage()