cmake_minimum_required(VERSION 3.19)
project(momo VERSION 0.1.0)

set(VCPKG_FEATURE_FLAGS "versions")

set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
include(CPack)


find_package(fmt CONFIG REQUIRED)
find_package(Catch2 CONFIG REQUIRED)
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

message("Python/include: " ${Python_INCLUDE_DIRS} )
message("Python/libs: " ${Python_LIBRARIES} )

# —————————————————————————
# create target for library
# —————————————————————————
pybind11_add_module(momo src/momo.cpp)
set_target_properties(${PROJECT_NAME} PROPERTIES VERSION ${PROJECT_VERSION})
set_target_properties(${PROJECT_NAME} PROPERTIES PUBLIC_HEADER include/momo/momo.h)
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)

target_link_libraries(${PROJECT_NAME} PRIVATE fmt::fmt)

include_directories(${Python_INCLUDE_DIRS})
target_link_libraries(${PROJECT_NAME} PRIVATE ${Python_LIBRARIES})


# https://github.com/microsoft/vcpkg/issues/5097
if(VCPKG_TOOLCHAIN)
    target_link_directories(${PROJECT_NAME} PRIVATE ${_VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib;${_VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/debug/lib)
endif()


# target_include_directories(${PROJECT_NAME}
#     PUBLIC
#         $<INSTALL_INTERFACE:include>
#         $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
#     PRIVATE
#         ${CMAKE_CURRENT_SOURCE_DIR}/src
# )

# Suppress prefix "lib" because Python does not allow this prefix
set_target_properties(${PROJECT_NAME} PROPERTIES PREFIX "")

# —————————————————————————————————————————
# create target for test, enable testing, and register a test "RunAllTests"
# —————————————————————————————————————————
include(CTest)
add_executable(run_tests tests/tests.cpp)
target_compile_features(run_tests PUBLIC cxx_std_17)
target_link_libraries(run_tests PRIVATE Catch2::Catch2)

enable_testing()
add_test(RunAllTests run_tests)