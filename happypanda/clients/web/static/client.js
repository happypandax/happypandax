$(document).ready(function () {
    var socket = io.connect("http://" + document.domain + ":" + location.port);
    socket.on("connection", function (msg) {
        console.log("Connection to server is alive: " + msg.status);
        if (!msg.status) {
            $("#global").append("<div class='red'>Disconnected from server</div>");
        }

    });
});