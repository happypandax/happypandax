#from org.transcrypt.stubs.browser import __pragma__
import utils

__pragma__ ('alias', 'S', '$') # JQuery

disconnected_once = False
connection_status = True

def reconnect():
    def rc():
        if connection_status:
            clearInterval(con_interval)
            return
        socket.connect()
    con_interval = setInterval(rc, 5000)

def on_connect(msg):
    connection_status = msg['status']
    con_text = "server connection: "
    text = "Connected" if connection_status else "Disconnected"
    con_text += text
    el = S("#serverstat")
    el.text(con_text)
    if connection_status:
        if disconnected_once:
            S("#global").append("<div class='green'>Reconnected to server</div>")
    else:
        disconnected_once = True
        reconnect()
        S("#global").append("<div class='red'>Disconnected from server</div>")

def api_call():
    d = { "fname": (S("#fname")).val() }

    def each_d(index, element):
        lichildren = S(this).children();
        key = lichildren.eq(0).find("input").val();
        value = lichildren.eq(1).find("input").val();
        if key and value:
            d[key] = value

    S("div#args > ul > li").each(each_d)
    socket.emit("server_call", d)

def add_kwarg():
    S("div#args > ul").append("<li><span><input type='text', placeholder='keyword'></span><span><input type='text', placeholder='value'></span></li>")

socket = io.connect()

# handlers

socket.on("connection", on_connect)

socket.on("server_call", lambda msg: S("pre#json").html(utils.syntax_highlight(JSON.stringify(msg['data'], None, 4))))

