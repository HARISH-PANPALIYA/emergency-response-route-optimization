#include "Graph.h"

#include <stdexcept>
#include <algorithm>

Graph::Graph() = default;

Graph::Graph(int nodeCount) {
    nodes_.resize(nodeCount);
    for (int i = 0; i < nodeCount; ++i) {
        nodes_[i].id = i;
    }
    adjacency_.assign(nodeCount, {});
}

void Graph::addNode(const Node& node) {
    if (node.id < 0) {
        throw std::invalid_argument("Node id must be non-negative");
    }
    if (static_cast<int>(nodes_.size()) <= node.id) {
        nodes_.resize(node.id + 1);
        adjacency_.resize(node.id + 1);
    }
    nodes_[node.id] = node;
}

void Graph::addEdge(int from, int to, double weight, bool blocked, bool undirected) {
    if (from < 0 || to < 0) {
        throw std::invalid_argument("Node ids must be non-negative");
    }
    if (static_cast<int>(nodes_.size()) <= std::max(from, to)) {
        nodes_.resize(std::max(from, to) + 1);
        adjacency_.resize(std::max(from, to) + 1);
    }

    Edge forward{to, weight, blocked};
    adjacency_[from].push_back(forward);

    if (undirected) {
        Edge reverse{from, weight, blocked};
        adjacency_[to].push_back(reverse);
    }
}

void Graph::setEdgeBlocked(int from, int to, bool blocked, bool undirected) {
    if (from < 0 || to < 0 || from >= static_cast<int>(adjacency_.size()) || to >= static_cast<int>(adjacency_.size())) {
        return;
    }

    for (Edge& edge : adjacency_[from]) {
        if (edge.destination == to) {
            edge.blocked = blocked;
        }
    }

    if (undirected) {
        for (Edge& edge : adjacency_[to]) {
            if (edge.destination == from) {
                edge.blocked = blocked;
            }
        }
    }
}

void Graph::setNode(int id, double x, double y) {
    if (id < 0) {
        return;
    }
    if (static_cast<int>(nodes_.size()) <= id) {
        nodes_.resize(id + 1);
        adjacency_.resize(id + 1);
    }
    nodes_[id].id = id;
    nodes_[id].x = x;
    nodes_[id].y = y;
}

int Graph::nodeCount() const {
    return static_cast<int>(nodes_.size());
}

const std::vector<Node>& Graph::nodes() const {
    return nodes_;
}

const std::vector<std::vector<Edge>>& Graph::adjacencyList() const {
    return adjacency_;
}

Graph Graph::buildDemoGraph() {
    Graph graph(36);
    const int rows = 6;
    const int columns = 6;

    for (int row = 0; row < rows; ++row) {
        for (int col = 0; col < columns; ++col) {
            int id = row * columns + col;
            graph.setNode(id, static_cast<double>(col * 120), static_cast<double>(row * 120));
        }
    }

    for (int row = 0; row < rows; ++row) {
        for (int col = 0; col < columns; ++col) {
            int current = row * columns + col;

            if (col + 1 < columns) {
                graph.addEdge(current, current + 1, 4.0, false, true);
            }
            if (row + 1 < rows) {
                graph.addEdge(current, current + columns, 5.0, false, true);
            }
            if (col + 1 < columns && row + 1 < rows) {
                graph.addEdge(current, current + columns + 1, 6.0, false, true);
            }
            if (col > 0 && row + 1 < rows) {
                graph.addEdge(current, current + columns - 1, 6.0, false, true);
            }

            if (row == 0 && col == 2) {
                graph.addEdge(current, 20, 8.5, false, true);
            }
            if (row == 1 && col == 4) {
                graph.addEdge(current, 29, 7.5, false, true);
            }
            if (row == 2 && col == 1) {
                graph.addEdge(current, 33, 9.0, false, true);
            }
            if (row == 3 && col == 3) {
                graph.addEdge(current, 12, 8.0, false, true);
            }
        }
    }

    return graph;
}
