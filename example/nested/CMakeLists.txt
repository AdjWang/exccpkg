cmake_minimum_required(VERSION 3.28)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(Foo)

add_subdirectory(deps/Bar)
add_subdirectory(deps/Baz)

find_package(absl 20240722 REQUIRED)
add_executable(Foo hello_world.cc)
target_link_libraries(Foo PRIVATE absl::strings Bar)
