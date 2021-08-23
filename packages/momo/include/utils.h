#pragma once
#include <string>
#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace momo {
    
std::string get_env_variable(std::string const& key);

struct Log {
    py::object i;
    py::object d;
    py::object w;
    py::object e;
};

Log get_logger(std::string name);

}
