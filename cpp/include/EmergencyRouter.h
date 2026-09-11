#pragma once

#include <vector>
#include <string>

#include "Graph.h"
#include "Dijkstra.h"
#include "Facility.h"
#include "EmergencyUnit.h"

struct AssignmentResult {
    bool success = false;
    std::string unitId;
    std::string unitName;
    UnitType unitType = UnitType::AMBULANCE;
    int facilityId = -1;
    std::string facilityName;
    FacilityType facilityType = FacilityType::HOSPITAL;
    RoutingResult route;
    double travelCost = 0.0;
};

class EmergencyRouter {
public:
    explicit EmergencyRouter(Graph graph);

    RoutingResult route(int source, int destination) const;
    std::vector<Facility> facilitiesForEmergency(EmergencyType emergencyType, const std::vector<Facility>& facilities) const;

    AssignmentResult findBestAvailableUnit(
        int incidentNode,
        UnitType requiredUnitType,
        const std::vector<EmergencyUnit>& units,
        const std::vector<Facility>& facilities,
        EmergencyType emergencyType) const;

    std::pair<Facility, RoutingResult> findBestFacility(
        int incidentNode,
        EmergencyType emergencyType,
        const std::vector<Facility>& facilities) const;

private:
    Graph graph_;
};
