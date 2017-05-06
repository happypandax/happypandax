__pragma__ ('alias', 'S', '$') # JQuery

from client import client, Base
import utils

class IndexPage(Base):
    pass

class ApiPage(Base):

    def call(self):
        d = { "fname": (S("#fname")).val() }

        def each_d(index, element):
            lichildren = S(this).children();
            key = lichildren.eq(0).find("input").val();
            value = lichildren.eq(1).find("input").val();
            if key and value:
                d[key] = value

        S("div#args > ul > li").each(each_d)
        client.call(d, lambda msg: S("pre#json").html(utils.syntax_highlight(JSON.stringify(msg, None, 4))))

    def add_kwarg(self):
        S("div#args > ul").append("<li><span><input type='text', placeholder='keyword'></span><span><input type='text', placeholder='value'></span></li>")

api = ApiPage()