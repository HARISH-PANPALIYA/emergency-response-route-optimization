#pragma once

#include <vector>
#include <string>

#include "Node.h"
#include "Edge.h"

class Graph {
public:
    Graph();
    explicit Graph(int nodeCount);

    void addNode(const Node& node);
    void addEdge(int from, int to, double weight, bool blocked = false, bool undirected = true);
    void setEdgeBlocked(int from, int to, bool blocked, bool undirected = true);
    void setNode(int id, double x, double y);
    int nodeCount() const;
    const std::vector<Node>& nodes() const;
    const std::vector<std::vector<Edge>>& adjacencyList() const;

    // Synthetic demo city for emergency dispatch testing.
    static Graph buildDemoGraph();

private:
    std::vector<Node> nodes_;
    std::vector<std::vector<Edge>> adjacency_;
};
