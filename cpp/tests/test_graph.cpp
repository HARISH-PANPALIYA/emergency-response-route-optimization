#include <cassert>

#include "Graph.h"

int main() {
    Graph graph = Graph::buildDemoGraph();
    assert(graph.nodeCount() >= 30);
    assert(graph.adjacencyList().size() == static_cast<size_t>(graph.nodeCount()));
    return 0;
}
