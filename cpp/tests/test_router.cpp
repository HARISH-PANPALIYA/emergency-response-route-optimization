#include <cassert>

#include "EmergencyRouter.h"

int main() {
    Graph graph = Graph::buildDemoGraph();
    EmergencyRouter router(graph);

    std::vector<Facility> facilities = FacilityManager::demoFacilities();
    std::vector<EmergencyUnit> units = UnitCatalog::demoUnits();

    AssignmentResult assignment = router.findBestAvailableUnit(12, UnitType::AMBULANCE, units, facilities, EmergencyType::MEDICAL);
    assert(assignment.success);

    auto bestFacility = router.findBestFacility(12, EmergencyType::MEDICAL, facilities);
    assert(bestFacility.first.id > 0);
    return 0;
}
