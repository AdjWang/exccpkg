cmake_minimum_required(VERSION 3.28)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(Foo)

# Expected find_package search path:
# set(absl_DIR ${CMAKE_CURRENT_LIST_DIR}/deps/out/${CMAKE_BUILD_TYPE}/lib/cmake/absl)
find_package(absl 20240722 REQUIRED)
add_executable(Foo hello_world.cc)
target_link_libraries(Foo PRIVATE absl::strings)
if (WIN32)
  set_property(TARGET Foo PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded")
endif()
