cmake_minimum_required(VERSION 3.16)
project(EmergencyRouting LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

add_library(emergency_routing_lib STATIC
    src/Graph.cpp
    src/Dijkstra.cpp
    src/EmergencyRouter.cpp
)

target_include_directories(emergency_routing_lib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(emergency_routing_lib PUBLIC cxx_std_17)

add_executable(test_graph tests/test_graph.cpp)
target_link_libraries(test_graph PRIVATE emergency_routing_lib)
target_include_directories(test_graph PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

add_executable(test_dijkstra tests/test_dijkstra.cpp)
target_link_libraries(test_dijkstra PRIVATE emergency_routing_lib)
target_include_directories(test_dijkstra PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

add_executable(test_router tests/test_router.cpp)
target_link_libraries(test_router PRIVATE emergency_routing_lib)
target_include_directories(test_router PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

pybind11_add_module(emergency_routing bindings/bindings.cpp)
target_link_libraries(emergency_routing PRIVATE emergency_routing_lib)
target_include_directories(emergency_routing PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
