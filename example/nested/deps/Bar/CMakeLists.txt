cmake_minimum_required(VERSION 3.28)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(Bar)

find_package(absl 20240722 REQUIRED)
add_library(Bar hello_world.cc)
target_link_libraries(Bar PRIVATE absl::strings)
if (WIN32)
  set_property(TARGET Bar PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded")
endif()
