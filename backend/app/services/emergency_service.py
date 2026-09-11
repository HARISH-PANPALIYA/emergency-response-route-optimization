from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.services.routing_bridge import graph_map_data, route


@dataclass
class EmergencyStore:
    facilities: list[dict[str, Any]] = field(default_factory=lambda: [
        {"id": 1, "name": "Central Government Hospital", "type": "HOSPITAL", "node": 5, "status": "ACTIVE"},
        {"id": 2, "name": "District General Hospital", "type": "HOSPITAL", "node": 12, "status": "ACTIVE"},
        {"id": 3, "name": "Government Trauma Centre", "type": "HOSPITAL", "node": 18, "status": "ACTIVE"},
        {"id": 4, "name": "Central Police Station", "type": "POLICE_STATION", "node": 22, "status": "ACTIVE"},
        {"id": 5, "name": "Central Fire Station", "type": "FIRE_STATION", "node": 8, "status": "ACTIVE"},
    ])
    units: list[dict[str, Any]] = field(default_factory=lambda: [
        {"id": "AMBULANCE-A01", "name": "AMBULANCE-A01", "type": "AMBULANCE", "current_node": 4, "status": "AVAILABLE"},
        {"id": "AMBULANCE-A02", "name": "AMBULANCE-A02", "type": "AMBULANCE", "current_node": 17, "status": "AVAILABLE"},
        {"id": "FIRE-F01", "name": "FIRE-F01", "type": "FIRE_TRUCK", "current_node": 7, "status": "AVAILABLE"},
        {"id": "FIRE-F02", "name": "FIRE-F02", "type": "FIRE_TRUCK", "current_node": 14, "status": "AVAILABLE"},
        {"id": "POLICE-P01", "name": "POLICE-P01", "type": "POLICE_VEHICLE", "current_node": 3, "status": "AVAILABLE"},
    ])
    emergencies: list[dict[str, Any]] = field(default_factory=list)
    roads: list[dict[str, Any]] = field(default_factory=lambda: [
        {"source": 0, "destination": 1, "weight": 4.0, "blocked": False},
        {"source": 1, "destination": 2, "weight": 5.0, "blocked": False},
        {"source": 2, "destination": 8, "weight": 6.0, "blocked": False},
    ])
    users: list[dict[str, Any]] = field(default_factory=list)


store = EmergencyStore()


def get_map_data() -> dict[str, Any]:
    cxx_map = graph_map_data()
    if cxx_map is not None:
        return {
            "nodes": list(cxx_map["nodes"]),
            "edges": list(cxx_map["edges"]),
        }

    return {
        "nodes": [
            {"id": 0, "x": 0, "y": 0},
            {"id": 1, "x": 120, "y": 0},
            {"id": 2, "x": 240, "y": 0},
            {"id": 3, "x": 360, "y": 0},
            {"id": 4, "x": 480, "y": 0},
            {"id": 5, "x": 600, "y": 0},
        ],
        "edges": store.roads,
    }


def determine_unit_type(emergency_type: str) -> str:
    mapping = {
        "MEDICAL": "AMBULANCE",
        "FIRE": "FIRE_TRUCK",
        "CRIME": "POLICE_VEHICLE",
        "ACCIDENT": "AMBULANCE",
    }
    return mapping.get(emergency_type, "AMBULANCE")


def find_best_unit_for_emergency(emergency: dict[str, Any]) -> dict[str, Any]:
    unit_type = determine_unit_type(emergency["emergency_type"])
    available = [u for u in store.units if u["type"] == unit_type and u["status"] == "AVAILABLE"]
    if not available:
        return {"success": False, "message": "No available units"}

    best_candidate = min(
        available,
        key=lambda unit: route(emergency["location"], unit["current_node"])["cost"],
    )
    return {
        "success": True,
        "assigned_unit": best_candidate,
        "route": route(emergency["location"], best_candidate["current_node"]),
    }


def create_emergency(data: dict[str, Any]) -> dict[str, Any]:
    emergency_id = len(store.emergencies) + 1
    item = {
        "id": emergency_id,
        "emergency_type": data["emergency_type"],
        "location": data["location"],
        "description": data["description"],
        "status": "REPORTED",
        "assigned_unit": None,
        "facility": None,
        "route": [],
        "travel_cost": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    store.emergencies.append(item)
    return item


def update_emergency_status(emergency_id: int, status: str) -> dict[str, Any]:
    for item in store.emergencies:
        if item["id"] == emergency_id:
            item["status"] = status
            return item
    raise ValueError("Emergency not found")


def list_emergencies() -> list[dict[str, Any]]:
    return store.emergencies
