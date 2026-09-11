#pragma once

#include <vector>

struct RoutingResult {
    bool success = false;
    int source = -1;
    int destination = -1;
    std::vector<int> route;
    double cost = 0.0;
    std::vector<int> alternativeRoute;
    double alternativeCost = 0.0;
    long long nodesExplored = 0;
};
