#pragma once

#include <string>
#include <vector>

enum class FacilityType {
    HOSPITAL,
    POLICE_STATION,
    FIRE_STATION,
    AMBULANCE_CENTER
};

enum class FacilityStatus {
    ACTIVE,
    INACTIVE
};

enum class EmergencyType {
    MEDICAL,
    FIRE,
    CRIME,
    ACCIDENT
};

struct Facility {
    int id = -1;
    std::string name;
    FacilityType type = FacilityType::HOSPITAL;
    int node = -1;
    FacilityStatus status = FacilityStatus::ACTIVE;
};

class FacilityManager {
public:
    static FacilityType facilityTypeForEmergency(EmergencyType emergencyType);
    static std::vector<Facility> matchingFacilities(const std::vector<Facility>& facilities, EmergencyType emergencyType);
    static std::vector<Facility> demoFacilities();
};
