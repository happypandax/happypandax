#include "../include/momo.h"
#include "../include/pixie.h"

PYBIND11_MODULE(momo, m)
{
    m.doc() = "Momo-chan!"; // optional module docstring

    m.def("start_pixie", &momo::start_pixie, "Setup Pixie");
}