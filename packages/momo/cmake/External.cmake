include(FindGit)
find_package(Git)

if (NOT Git_FOUND)
    message(FATAL_ERROR "Git not found!")
endif ()

include (FetchContent)

set (Sqlpp11_PostgeSQL "Sqlpp11_PostgeSQL")

FetchContent_Declare(${Sqlpp11_PostgeSQL}
    GIT_REPOSITORY https://github.com/dgel/sqlpp11-connector-postgresql
    GIT_TAG add_pic_static_lib
    GIT_SHALLOW    ON
    SOURCE_DIR        ./build/ext/${Sqlpp11_PostgeSQL}
    INSTALL_DIR       ${CMAKE_CURRENT_BINARY_DIR}/ext/${Sqlpp11_PostgeSQL}
)
FetchContent_MakeAvailable(${Sqlpp11_PostgeSQL})

message("Added external library: " ${Sqlpp11_PostgeSQL})

