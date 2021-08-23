#include "../include/utils.h"


std::string momo::get_env_variable(std::string const& key)
{
    char* val = getenv(key.c_str());
    return val == NULL ? std::string("") : std::string(val);
}

momo::Log momo::get_logger( std::string name ) {
    py::object Logger = py::module_::import("happypanda.common.hlogger").attr("Logger");

    const auto hlog = Logger("momo." + name);

    return { .w = hlog.attr("w"), .i = hlog.attr("i"), .d = hlog.attr("d"), .e = hlog.attr("e"),};
}

