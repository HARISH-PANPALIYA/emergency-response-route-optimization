#include "EmergencyRouter.h"

#include <limits>
#include <algorithm>

namespace {
    const auto kFacilityPreferredOrder = {
        FacilityType::HOSPITAL,
        FacilityType::FIRE_STATION,
        FacilityType::POLICE_STATION,
        FacilityType::AMBULANCE_CENTER
    };
}

FacilityType FacilityManager::facilityTypeForEmergency(EmergencyType emergencyType) {
    switch (emergencyType) {
        case EmergencyType::MEDICAL:
            return FacilityType::HOSPITAL;
        case EmergencyType::FIRE:
            return FacilityType::FIRE_STATION;
        case EmergencyType::CRIME:
            return FacilityType::POLICE_STATION;
        case EmergencyType::ACCIDENT:
            return FacilityType::HOSPITAL;
        default:
            return FacilityType::HOSPITAL;
    }
}

std::vector<Facility> FacilityManager::matchingFacilities(const std::vector<Facility>& facilities, EmergencyType emergencyType) {
    std::vector<Facility> matched;
    const FacilityType preferred = facilityTypeForEmergency(emergencyType);

    for (const Facility& facility : facilities) {
        if (facility.status == FacilityStatus::ACTIVE && facility.type == preferred) {
            matched.push_back(facility);
        }
    }

    if (emergencyType == EmergencyType::ACCIDENT) {
        for (const Facility& facility : facilities) {
            if (facility.status == FacilityStatus::ACTIVE && facility.type == FacilityType::POLICE_STATION) {
                matched.push_back(facility);
            }
        }
    }

    return matched;
}

std::vector<Facility> FacilityManager::demoFacilities() {
    return {
        {1, "Central Government Hospital", FacilityType::HOSPITAL, 5, FacilityStatus::ACTIVE},
        {2, "District General Hospital", FacilityType::HOSPITAL, 12, FacilityStatus::ACTIVE},
        {3, "Government Trauma Centre", FacilityType::HOSPITAL, 18, FacilityStatus::ACTIVE},
        {4, "Central Police Station", FacilityType::POLICE_STATION, 22, FacilityStatus::ACTIVE},
        {5, "East Police Station", FacilityType::POLICE_STATION, 28, FacilityStatus::ACTIVE},
        {6, "West Police Station", FacilityType::POLICE_STATION, 31, FacilityStatus::ACTIVE},
        {7, "Central Fire Station", FacilityType::FIRE_STATION, 8, FacilityStatus::ACTIVE},
        {8, "North Fire Station", FacilityType::FIRE_STATION, 15, FacilityStatus::ACTIVE},
        {9, "Industrial Fire Station", FacilityType::FIRE_STATION, 25, FacilityStatus::ACTIVE},
        {10, "Central Ambulance Centre", FacilityType::AMBULANCE_CENTER, 17, FacilityStatus::ACTIVE},
        {11, "District Ambulance Centre", FacilityType::AMBULANCE_CENTER, 27, FacilityStatus::ACTIVE}
    };
}

std::vector<EmergencyUnit> UnitCatalog::demoUnits() {
    return {
        {"AMBULANCE-A01", "AMBULANCE-A01", UnitType::AMBULANCE, 4, UnitStatus::AVAILABLE},
        {"AMBULANCE-A02", "AMBULANCE-A02", UnitType::AMBULANCE, 17, UnitStatus::AVAILABLE},
        {"AMBULANCE-A03", "AMBULANCE-A03", UnitType::AMBULANCE, 23, UnitStatus::AVAILABLE},
        {"FIRE-F01", "FIRE-F01", UnitType::FIRE_TRUCK, 7, UnitStatus::AVAILABLE},
        {"FIRE-F02", "FIRE-F02", UnitType::FIRE_TRUCK, 14, UnitStatus::AVAILABLE},
        {"FIRE-F03", "FIRE-F03", UnitType::FIRE_TRUCK, 21, UnitStatus::AVAILABLE},
        {"POLICE-P01", "POLICE-P01", UnitType::POLICE_VEHICLE, 3, UnitStatus::AVAILABLE},
        {"POLICE-P02", "POLICE-P02", UnitType::POLICE_VEHICLE, 25, UnitStatus::AVAILABLE},
        {"POLICE-P03", "POLICE-P03", UnitType::POLICE_VEHICLE, 30, UnitStatus::AVAILABLE}
    };
}

std::vector<EmergencyUnit> UnitCatalog::availableUnits(const std::vector<EmergencyUnit>& units, UnitType type) {
    std::vector<EmergencyUnit> result;
    for (const auto& unit : units) {
        if (unit.type == type && unit.status == UnitStatus::AVAILABLE) {
            result.push_back(unit);
        }
    }
    return result;
}

EmergencyRouter::EmergencyRouter(Graph graph)
    : graph_(std::move(graph)) {}

RoutingResult EmergencyRouter::route(int source, int destination) const {
    return Dijkstra::shortestPath(graph_, source, destination);
}

std::vector<Facility> EmergencyRouter::facilitiesForEmergency(EmergencyType emergencyType, const std::vector<Facility>& facilities) const {
    return FacilityManager::matchingFacilities(facilities, emergencyType);
}

std::pair<Facility, RoutingResult> EmergencyRouter::findBestFacility(
    int incidentNode,
    EmergencyType emergencyType,
    const std::vector<Facility>& facilities) const {

    std::vector<Facility> candidates = facilitiesForEmergency(emergencyType, facilities);
    if (candidates.empty()) {
        return {{-1, "", FacilityManager::facilityTypeForEmergency(emergencyType), -1, FacilityStatus::INACTIVE}, RoutingResult()};
    }

    Facility bestFacility = candidates.front();
    RoutingResult bestPath;
    double lowestCost = std::numeric_limits<double>::infinity();

    for (const Facility& facility : candidates) {
        RoutingResult route = Dijkstra::shortestPath(graph_, incidentNode, facility.node);
        if (route.success && route.cost < lowestCost) {
            bestFacility = facility;
            bestPath = route;
            lowestCost = route.cost;
        }
    }

    return {bestFacility, bestPath};
}

AssignmentResult EmergencyRouter::findBestAvailableUnit(
    int incidentNode,
    UnitType requiredUnitType,
    const std::vector<EmergencyUnit>& units,
    const std::vector<Facility>& facilities,
    EmergencyType emergencyType) const {

    std::vector<EmergencyUnit> candidates = UnitCatalog::availableUnits(units, requiredUnitType);
    if (candidates.empty()) {
        return AssignmentResult();
    }

    AssignmentResult best;
    double bestCost = std::numeric_limits<double>::infinity();

    for (const auto& unit : candidates) {
        RoutingResult path = Dijkstra::shortestPath(graph_, incidentNode, unit.currentNode);
        if (!path.success) {
            continue;
        }

        if (path.cost < bestCost) {
            best.success = true;
            best.unitId = unit.id;
            best.unitName = unit.name;
            best.unitType = unit.type;
            best.route = path;
            best.travelCost = path.cost;
            bestCost = path.cost;
        }
    }

    if (!best.success) {
        return best;
    }

    auto bestFacility = findBestFacility(incidentNode, emergencyType, facilities);
    best.facilityId = bestFacility.first.id;
    best.facilityName = bestFacility.first.name;
    best.facilityType = bestFacility.first.type;
    if (bestFacility.second.success) {
        best.route = bestFacility.second;
    }

    return best;
}
