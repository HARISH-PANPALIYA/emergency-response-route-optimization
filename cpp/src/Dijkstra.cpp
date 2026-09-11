#include "Dijkstra.h"

#include <queue>
#include <limits>
#include <algorithm>
#include <cmath>

namespace {
    constexpr double kInfinity = std::numeric_limits<double>::infinity();
}

std::vector<int> Dijkstra::reconstructPath(const std::vector<int>& parent, int source, int destination, int nodeCount) {
    if (source == destination) {
        return {source};
    }

    if (source < 0 || destination < 0 || source >= nodeCount || destination >= nodeCount) {
        return {};
    }

    std::vector<int> path;
    int current = destination;
    while (current != -1) {
        path.push_back(current);
        if (current == source) {
            break;
        }
        current = parent[current];
    }

    if (path.empty() || path.back() != source) {
        return {};
    }

    std::reverse(path.begin(), path.end());
    return path;
}

double Dijkstra::pathCost(const Graph& graph, const std::vector<int>& route) {
    if (route.size() < 2) {
        return 0.0;
    }

    double total = 0.0;
    for (size_t index = 0; index + 1 < route.size(); ++index) {
        int from = route[index];
        int to = route[index + 1];
        const auto& neighbors = graph.adjacencyList()[from];
        for (const Edge& edge : neighbors) {
            if (edge.destination == to && !edge.blocked) {
                total += edge.weight;
                break;
            }
        }
    }

    return total;
}

std::vector<double> Dijkstra::distancesFromSource(const Graph& graph, int source) {
    const int nodeCount = graph.nodeCount();
    std::vector<double> distance(nodeCount, kInfinity);
    if (source < 0 || source >= nodeCount) {
        return distance;
    }

    std::priority_queue<std::pair<double, int>, std::vector<std::pair<double, int>>, std::greater<std::pair<double, int>>> minHeap;
    distance[source] = 0.0;
    minHeap.push({0.0, source});

    while (!minHeap.empty()) {
        auto [currentDistance, currentNode] = minHeap.top();
        minHeap.pop();
        if (currentDistance > distance[currentNode] + 1e-9) {
            continue;
        }

        for (const Edge& edge : graph.adjacencyList()[currentNode]) {
            if (edge.blocked) {
                continue;
            }
            const double alternative = currentDistance + edge.weight;
            if (alternative < distance[edge.destination] - 1e-9) {
                distance[edge.destination] = alternative;
                minHeap.push({alternative, edge.destination});
            }
        }
    }
    return distance;
}

namespace {
    RoutingResult shortestPathCore(const Graph& graph, int source, int destination) {
        RoutingResult result;
        result.source = source;
        result.destination = destination;

        const int nodeCount = graph.nodeCount();
        if (source < 0 || destination < 0 || source >= nodeCount || destination >= nodeCount) {
            return result;
        }

        std::vector<double> distance(nodeCount, kInfinity);
        std::vector<int> parent(nodeCount, -1);
        std::priority_queue<std::pair<double, int>, std::vector<std::pair<double, int>>, std::greater<std::pair<double, int>>> minHeap;

        distance[source] = 0.0;
        minHeap.push({0.0, source});
        long long explored = 0;

        while (!minHeap.empty()) {
            auto [currentDistance, currentNode] = minHeap.top();
            minHeap.pop();

            if (currentDistance > distance[currentNode] + 1e-9) {
                continue;
            }

            ++explored;

            if (currentNode == destination) {
                break;
            }

            for (const Edge& edge : graph.adjacencyList()[currentNode]) {
                if (edge.blocked) {
                    continue;
                }

                const double alternative = currentDistance + edge.weight;
                if (alternative < distance[edge.destination] - 1e-9) {
                    distance[edge.destination] = alternative;
                    parent[edge.destination] = currentNode;
                    minHeap.push({alternative, edge.destination});
                }
            }
        }

        result.nodesExplored = explored;

        std::vector<int> route = Dijkstra::reconstructPath(parent, source, destination, nodeCount);
        if (!route.empty()) {
            result.route = route;
            result.cost = Dijkstra::pathCost(graph, route);
            result.success = true;
        }

        if (route.empty() || route.back() != destination) {
            result.success = false;
            result.route.clear();
            result.cost = 0.0;
        }

        return result;
    }
}

RoutingResult Dijkstra::shortestPath(const Graph& graph, int source, int destination) {
    RoutingResult result = shortestPathCore(graph, source, destination);
    if (!result.success || result.route.size() <= 1) {
        return result;
    }

    // Alternative route is calculated by temporarily removing one edge from the shortest route
    // and rerunning Dijkstra without starting another recursive alternative search. This is intentionally
    // simple and honest: it is not a full K-shortest path solver.
    double bestAltCost = kInfinity;
    std::vector<int> bestAltRoute;

    for (size_t index = 0; index + 1 < result.route.size(); ++index) {
        Graph modifiedGraph = graph;
        modifiedGraph.setEdgeBlocked(result.route[index], result.route[index + 1], true, true);
        RoutingResult alternative = shortestPathCore(modifiedGraph, source, destination);
        if (alternative.success && alternative.cost < bestAltCost && !alternative.route.empty()) {
            bool isSameRoute = alternative.route.size() == result.route.size() && alternative.route == result.route;
            if (!isSameRoute) {
                bestAltCost = alternative.cost;
                bestAltRoute = alternative.route;
            }
        }
    }

    if (!bestAltRoute.empty()) {
        result.alternativeRoute = bestAltRoute;
        result.alternativeCost = bestAltCost;
    }

    return result;
}
