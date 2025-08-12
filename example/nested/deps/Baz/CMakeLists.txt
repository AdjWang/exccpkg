cmake_minimum_required(VERSION 3.28)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(Baz)

find_package(GTest REQUIRED)
add_executable(Baz test_baz.cc)
target_link_libraries(Baz PRIVATE GTest::gmock_main)
if (WIN32)
  set_property(TARGET Baz PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded")
endif()
