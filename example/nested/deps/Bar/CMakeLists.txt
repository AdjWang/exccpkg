cmake_minimum_required(VERSION 3.28)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(Bar)

set(absl_DIR ${CMAKE_CURRENT_LIST_DIR}/deps/out/${CMAKE_BUILD_TYPE}/lib/cmake/absl)
find_package(absl 20230802 REQUIRED)
add_library(Bar hello_world.cc)
target_link_libraries(Bar PRIVATE absl::strings)
