#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <tuple>

#include "Graph.h"
#include "Dijkstra.h"
#include "EmergencyRouter.h"

namespace py = pybind11;

PYBIND11_MODULE(emergency_routing, m) {
    py::class_<Node>(m, "Node")
        .def(py::init<>())
        .def_readwrite("id", &Node::id)
        .def_readwrite("x", &Node::x)
        .def_readwrite("y", &Node::y);

    py::class_<Edge>(m, "Edge")
        .def(py::init<>())
        .def_readwrite("destination", &Edge::destination)
        .def_readwrite("weight", &Edge::weight)
        .def_readwrite("blocked", &Edge::blocked);

    py::class_<Graph>(m, "Graph")
        .def(py::init<>())
        .def(py::init<int>())
        .def("add_node", &Graph::addNode)
        .def("add_edge", &Graph::addEdge)
        .def("node_count", &Graph::nodeCount)
        .def("set_edge_blocked", &Graph::setEdgeBlocked)
        .def_static("build_demo_graph", &Graph::buildDemoGraph)
        .def("nodes", [](const Graph& graph) {
            py::list output;
            for (const Node& node : graph.nodes()) {
                output.append(node);
            }
            return output;
        })
        .def("adjacency_list", [](const Graph& graph) {
            py::list output;
            for (const auto& neighbors : graph.adjacencyList()) {
                py::list row;
                for (const Edge& edge : neighbors) {
                    row.append(edge);
                }
                output.append(row);
            }
            return output;
        });

    py::class_<RoutingResult>(m, "RoutingResult")
        .def(py::init<>())
        .def_readwrite("success", &RoutingResult::success)
        .def_readwrite("source", &RoutingResult::source)
        .def_readwrite("destination", &RoutingResult::destination)
        .def_readwrite("route", &RoutingResult::route)
        .def_readwrite("cost", &RoutingResult::cost)
        .def_readwrite("alternative_route", &RoutingResult::alternativeRoute)
        .def_readwrite("alternative_cost", &RoutingResult::alternativeCost)
        .def_readwrite("nodes_explored", &RoutingResult::nodesExplored);

    py::enum_<UnitType>(m, "UnitType")
        .value("AMBULANCE", UnitType::AMBULANCE)
        .value("FIRE_TRUCK", UnitType::FIRE_TRUCK)
        .value("POLICE_VEHICLE", UnitType::POLICE_VEHICLE)
        .export_values();

    py::class_<EmergencyUnit>(m, "EmergencyUnit")
        .def(py::init<>())
        .def_readwrite("id", &EmergencyUnit::id)
        .def_readwrite("name", &EmergencyUnit::name)
        .def_readwrite("type", &EmergencyUnit::type)
        .def_readwrite("current_node", &EmergencyUnit::currentNode)
        .def_readwrite("status", &EmergencyUnit::status);

    py::enum_<FacilityType>(m, "FacilityType")
        .value("HOSPITAL", FacilityType::HOSPITAL)
        .value("POLICE_STATION", FacilityType::POLICE_STATION)
        .value("FIRE_STATION", FacilityType::FIRE_STATION)
        .value("AMBULANCE_CENTER", FacilityType::AMBULANCE_CENTER)
        .export_values();

    py::class_<Facility>(m, "Facility")
        .def(py::init<>())
        .def_readwrite("id", &Facility::id)
        .def_readwrite("name", &Facility::name)
        .def_readwrite("type", &Facility::type)
        .def_readwrite("node", &Facility::node)
        .def_readwrite("status", &Facility::status);

    py::class_<AssignmentResult>(m, "AssignmentResult")
        .def(py::init<>())
        .def_readwrite("success", &AssignmentResult::success)
        .def_readwrite("unit_id", &AssignmentResult::unitId)
        .def_readwrite("unit_name", &AssignmentResult::unitName)
        .def_readwrite("unit_type", &AssignmentResult::unitType)
        .def_readwrite("facility_id", &AssignmentResult::facilityId)
        .def_readwrite("facility_name", &AssignmentResult::facilityName)
        .def_readwrite("facility_type", &AssignmentResult::facilityType)
        .def_readwrite("route", &AssignmentResult::route)
        .def_readwrite("travel_cost", &AssignmentResult::travelCost);

    m.def("load_graph", []() { return Graph::buildDemoGraph(); });
    m.def("graph_from_edges", [](int nodeCount, const std::vector<std::tuple<int, int, double, bool>>& edges) {
        Graph graph(nodeCount);
        for (const auto& [source, destination, weight, blocked] : edges) {
            graph.addEdge(source, destination, weight, blocked, true);
        }
        return graph;
    });
    m.def("find_shortest_route", [](const Graph& graph, int source, int destination) {
        return Dijkstra::shortestPath(graph, source, destination);
    });
    m.def("find_distances_from_source", [](const Graph& graph, int source) {
        return Dijkstra::distancesFromSource(graph, source);
    });
    m.def("find_best_facility", [](const Graph& graph, int incidentNode, EmergencyType emergencyType, const std::vector<Facility>& facilities) {
        EmergencyRouter router(graph);
        auto result = router.findBestFacility(incidentNode, emergencyType, facilities);
        return result;
    });
    m.def("find_best_available_unit", [](const Graph& graph, int incidentNode, UnitType unitType, const std::vector<EmergencyUnit>& units, const std::vector<Facility>& facilities, EmergencyType emergencyType) {
        EmergencyRouter router(graph);
        return router.findBestAvailableUnit(incidentNode, unitType, units, facilities, emergencyType);
    });
    m.def("block_road", [](Graph& graph, int source, int destination) {
        graph.setEdgeBlocked(source, destination, true, true);
        return true;
    });
    m.def("unblock_road", [](Graph& graph, int source, int destination) {
        graph.setEdgeBlocked(source, destination, false, true);
        return true;
    });
    m.def("get_graph_map_data", [](const Graph& graph) {
        py::dict output;
        py::list nodes;
        for (const Node& node : graph.nodes()) {
            py::dict item;
            item["id"] = node.id;
            item["x"] = node.x;
            item["y"] = node.y;
            nodes.append(item);
        }
        output["nodes"] = nodes;

        py::list edges;
        for (size_t source = 0; source < graph.adjacencyList().size(); ++source) {
            for (const Edge& edge : graph.adjacencyList()[source]) {
                py::dict item;
                item["source"] = static_cast<int>(source);
                item["destination"] = edge.destination;
                item["weight"] = edge.weight;
                item["blocked"] = edge.blocked;
                edges.append(item);
            }
        }
        output["edges"] = edges;
        return output;
    });
}
