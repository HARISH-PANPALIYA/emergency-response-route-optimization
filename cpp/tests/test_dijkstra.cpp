#include <cassert>

#include "Dijkstra.h"
#include "Graph.h"

int main() {
    Graph graph = Graph::buildDemoGraph();
    RoutingResult route = Dijkstra::shortestPath(graph, 0, 35);
    assert(route.success);
    assert(route.route.front() == 0);
    assert(route.route.back() == 35);
    assert(route.cost >= 0.0);
    return 0;
}
