#pragma once

#include <string>
#include <vector>

enum class UnitType {
    AMBULANCE,
    FIRE_TRUCK,
    POLICE_VEHICLE
};

enum class UnitStatus {
    AVAILABLE,
    DISPATCHED,
    BUSY,
    OFFLINE
};

struct EmergencyUnit {
    std::string id;
    std::string name;
    UnitType type = UnitType::AMBULANCE;
    int currentNode = -1;
    UnitStatus status = UnitStatus::AVAILABLE;
};

class UnitCatalog {
public:
    static std::vector<EmergencyUnit> demoUnits();
    static std::vector<EmergencyUnit> availableUnits(const std::vector<EmergencyUnit>& units, UnitType type);
};
