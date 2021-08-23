#include <zmq_addon.hpp>
#include "nlohmann/json.hpp"

#include "../include/pixie.h"
#include "../include/utils.h"

momo::Pixie::Pixie() {
    this->socket = new zmq::socket_t(this->ctx, zmq::socket_type::sub);
    this->connected = false;
}

bool momo::Pixie::connect() {
    const auto log = get_logger("pixie");
    const auto endpoint = get_env_variable("PIXIE_ENDPOINT");

    log.i("Pixie endpoint: ", endpoint);

    if (endpoint.length()) {
        this->socket->bind(endpoint);
        this->socket->connect(endpoint);
        this->connected = true;
        log.i("Successfully connected on endpoint: ", endpoint);
        return true;
    }

    log.i("Failed to connect on endpoint: ", endpoint);
    return false;
}

bool momo::Pixie::send(json& data) const {
    const auto msg = json::to_msgpack(data);
    const auto r = this->socket->send(zmq::buffer( msg ));
    return r.has_value() ? false : true;
}

json momo::Pixie::receive() const {

    zmq::message_t msg;
    auto r = this->socket->recv(msg);
    if (r.has_value()) {
        auto* const m = msg.data<std::vector<uint8_t>>();
        auto data = json::from_msgpack(*m);
        return data;
    }
    return json();
}

void momo::start_pixie() {
    Pixie p{};

    if (p.connect()) {
        

    }

}


