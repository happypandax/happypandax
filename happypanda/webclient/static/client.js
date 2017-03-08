$(document).ready(function () {
    function server_connection(status) {
        var text = status ? "Connected" : "Disconnected";
        console.log("Server connection: " + text);
        var el = $("#serverstat")
        if (status) {
            el.text("server connection: connected")
        } else {
            $("#global").append("<div class='red'>Disconnected from server</div>");
            el.text("server connection: disconnected")
        }
    }

    var socket = io.connect({ transports: ["websocket"] }); // force websocket

    // handlers

    socket.on("connection", function (msg) {
        server_connection(msg.status)
    });
});