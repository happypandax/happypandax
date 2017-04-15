$(document).ready(function () {
    var disconnected_once = false;
    var connection_status = true;

    var socket = io.connect({ transports: ["websocket"] }); // force websocket

    function reconnect() {
        connection_interval = setInterval(function () {
            if (connection_status) {
                clearInterval(connection_interval);
                return;
            }
            socket.connect()
        }, 5000);
    }

    function server_connection(status) {
        connection_status = status;
        var text = status ? "Connected" : "Disconnected";
        console.log("Server connection: " + text);
        var el = $("#serverstat")
        if (status) {
            el.text("server connection: connected")
            if (disconnected_once)
                $("#global").append("<div class='green'>Reconnected to server</div>");
        } else {
            disconnected_once = true;
            reconnect();
            $("#global").append("<div class='red'>Disconnected from server</div>");
            el.text("server connection: disconnected")
        }
    }

    function syntax_highlight(json) {
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            var cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }

    // handlers

    socket.on("connection", function (msg) {
        server_connection(msg.status)
    });

    // debug

    socket.on("server_call", function (msg) {

        $("pre#json").html(syntax_highlight(JSON.stringify(msg.data, null, 4)))
    });

    $("#apicall").click(function () {
        var dict = { "fname": ($("#fname")).val() };
        $("div#args > ul > li").each(function (index, element) {
            var lichildren = $(this).children();
            var key = lichildren.eq(0).find("input").val();
            var value = lichildren.eq(1).find("input").val();
            if (key && value) {
                dict[key] = value;;
            }
        });
        socket.emit("server_call", dict);

    });

    $("#kwargsadd").click(function () {
        $("div#args > ul").append("<li><span><input type='text', placeholder='keyword'></span><span><input type='text', placeholder='value'></span></li>")
    });
});