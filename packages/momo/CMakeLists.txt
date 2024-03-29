cmake_minimum_required(VERSION 3.19)

get_cmake_property(vars CACHE_VARIABLES)
foreach(var ${vars})
  get_property(currentHelpString CACHE "${var}" PROPERTY HELPSTRING)
    if("${currentHelpString}" MATCHES "No help, variable specified on the command line." OR "${currentHelpString}" STREQUAL "")
        # message("${var} = [${${var}}]  --  ${currentHelpString}") # uncomment to see the variables being processed
        list(APPEND CL_ARGS "-D${var}=${${var}}")
    endif()
endforeach()

project(momo VERSION 0.1.0)

set(VCPKG_FEATURE_FLAGS "versions")

set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
include(CPack)

# —————————————————————————
# find packages
# —————————————————————————
find_package(pybind11 CONFIG REQUIRED)
find_package(cppzmq CONFIG REQUIRED)
 find_package(SOCI CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(date)


message("Python/include: " ${Python_INCLUDE_DIRS} )
message("Python/libs: " ${Python_LIBRARIES} )

# —————————————————————————
# Collect sources
# —————————————————————————

file(GLOB_RECURSE sources CONFIGURE_DEPENDS  ./src/*.h ./src/*.cpp)

# —————————————————————————
# create target for library
# —————————————————————————
pybind11_add_module(momo ${sources})
set_target_properties(${PROJECT_NAME} PROPERTIES VERSION ${PROJECT_VERSION})
set_target_properties(${PROJECT_NAME} PROPERTIES PUBLIC_HEADER include/momo/momo.h)
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_20)


# —————————————————————————
# link libraries
# —————————————————————————
target_link_libraries(${PROJECT_NAME} PRIVATE cppzmq cppzmq-static)
target_link_libraries(${PROJECT_NAME} PRIVATE nlohmann_json nlohmann_json::nlohmann_json)
target_link_libraries(${PROJECT_NAME} PRIVATE SOCI::soci_core SOCI::soci_empty SOCI::soci_sqlite3 SOCI::soci_postgresql)


# https://github.com/microsoft/vcpkg/issues/5097
 if(VCPKG_TOOLCHAIN)
    message("VCPKG Libs: " ${PROJECT_NAME} PRIVATE ${_VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib;${_VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/debug/lib )
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
