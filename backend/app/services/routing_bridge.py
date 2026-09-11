import importlib.util
import os
import sys
from pathlib import Path


def _load_extension():
    project_root = Path(__file__).resolve().parents[3]
    if os.name == "nt":
        dll_directories = [
            Path(sys.executable).resolve().parent,
            Path(os.environ.get("MSYS2_UCRT64", r"C:\msys64\ucrt64")) / "bin",
        ]
        for directory in dll_directories:
            if directory.exists() and hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(directory))

    build_directory = project_root / "build" / "cpp"
    candidate_paths = [
        build_directory / "emergency_routing.cp312-win_amd64.pyd",
        build_directory / "emergency_routing.pyd",
        build_directory / "emergency_routing.so",
        build_directory / "emergency_routing.cpython-312-x86_64-linux-gnu.so",
        build_directory / "emergency_routing" / "emergency_routing.pyd",
    ]
    candidate_paths.extend(sorted(build_directory.glob("emergency_routing*.so")))
    candidate_paths.extend(sorted(build_directory.glob("emergency_routing*.pyd")))

    for path in candidate_paths:
        if path.exists():
            spec = importlib.util.spec_from_file_location("emergency_routing", path)
            if spec is not None and spec.loader is not None:
                module = importlib.util.module_from_spec(spec)
                sys.modules["emergency_routing"] = module
                spec.loader.exec_module(module)
                return module

    return None


_extension = _load_extension()


def _require_extension():
    if _extension is None:
        raise RuntimeError("The emergency_routing pybind11 extension is not available")
    return _extension


def _graph_from_roads(roads: list[dict] | None):
    extension = _require_extension()
    if not roads:
        return extension.load_graph()
    edges = [
        (int(road["source"]), int(road["destination"]), float(road["weight"]), bool(road["blocked"]))
        for road in roads
    ]
    return extension.graph_from_edges(36, edges)


def route(source: int, destination: int, roads: list[dict] | None = None):
    extension = _require_extension()
    graph = _graph_from_roads(roads)
    result = extension.find_shortest_route(graph, source, destination)
    return {
        "success": bool(result.success),
        "source": int(result.source),
        "destination": int(result.destination),
        "route": [int(v) for v in result.route],
        "cost": float(result.cost),
        "alternative_route": [int(v) for v in result.alternative_route],
        "alternative_cost": float(result.alternative_cost),
        "nodes_explored": int(result.nodes_explored),
    }


def graph_map_data(roads: list[dict] | None = None):
    extension = _require_extension()
    return extension.get_graph_map_data(_graph_from_roads(roads))


def distances_from_source(source: int, roads: list[dict] | None = None) -> list[float]:
    extension = _require_extension()
    return [float(value) for value in extension.find_distances_from_source(_graph_from_roads(roads), source)]


def auto_assign_unit(incident_node: int, emergency_type: str, units: list, facilities: list):
    extension = _require_extension()
    graph = extension.load_graph()
    unit_type_map = {
        "MEDICAL": "AMBULANCE",
        "FIRE": "FIRE_TRUCK",
        "CRIME": "POLICE_VEHICLE",
        "ACCIDENT": "AMBULANCE",
    }
    unit_type = getattr(extension, unit_type_map[emergency_type])
    unit_list = []
    for item in units:
        unit = extension.EmergencyUnit()
        unit.id = item["id"]
        unit.name = item["name"]
        unit.type = getattr(extension, item["type"])
        unit.current_node = item["current_node"]
        unit.status = getattr(extension, "AVAILABLE")
        unit_list.append(unit)

    facility_list = []
    for item in facilities:
        facility = extension.Facility()
        facility.id = item["id"]
        facility.name = item["name"]
        facility.type = getattr(extension, item["type"])
        facility.node = item["node"]
        facility.status = getattr(extension, "ACTIVE")
        facility_list.append(facility)

    assignment = extension.find_best_available_unit(graph, incident_node, unit_type, unit_list, facility_list, getattr(extension, emergency_type))
    return {
        "success": bool(assignment.success),
        "assigned_unit": {"id": assignment.unit_id, "name": assignment.unit_name},
        "route": [int(v) for v in assignment.route],
        "travel_cost": float(assignment.travel_cost),
        "facility": assignment.facility_name,
    }
