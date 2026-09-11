#pragma once

#include <vector>

#include "Graph.h"
#include "RouteResult.h"

class Dijkstra {
public:
    static RoutingResult shortestPath(const Graph& graph, int source, int destination);
    static std::vector<double> distancesFromSource(const Graph& graph, int source);
    static std::vector<int> reconstructPath(const std::vector<int>& parent, int source, int destination, int nodeCount);
    static double pathCost(const Graph& graph, const std::vector<int>& route);
};
