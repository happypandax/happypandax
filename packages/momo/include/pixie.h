#pragma once

#include <zmq.hpp>

#include "nlohmann/json_fwd.hpp"

using json = nlohmann::json;

namespace momo {

    class Pixie {

    public:
        Pixie();

        bool connect();
        bool send(json& data) const;
        json receive() const;

    private:
        zmq::socket_t* socket;
        zmq::context_t ctx;
        bool connected;

    };


    void start_pixie();

}