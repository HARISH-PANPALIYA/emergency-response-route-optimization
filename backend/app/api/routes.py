from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db import (
    Assignment, Emergency, EmergencyHistory, EmergencyStatus, EmergencyType, EmergencyUnit,
    Facility, FacilityType, Road, UnitStatus, UnitType, User, UserRole, get_db,
)
from app.schemas.auth import TokenResponse, UserCreate, UserLogin
from app.schemas.emergency import EmergencyCreate, RouteRequest
from app.schemas.facility import FacilityCreate
from app.schemas.unit import EmergencyUnitCreate
from app.services.routing_bridge import distances_from_source, graph_map_data, route
from app.services.seed import seed_demo_data

router = APIRouter()
security = HTTPBearer()

TRANSITIONS = {
    EmergencyStatus.REPORTED: {EmergencyStatus.ASSIGNING, EmergencyStatus.CANCELLED},
    EmergencyStatus.ASSIGNING: {EmergencyStatus.DISPATCHED, EmergencyStatus.CANCELLED},
    EmergencyStatus.DISPATCHED: {EmergencyStatus.IN_PROGRESS, EmergencyStatus.CANCELLED},
    EmergencyStatus.IN_PROGRESS: {EmergencyStatus.RESOLVED},
    EmergencyStatus.RESOLVED: set(),
    EmergencyStatus.CANCELLED: set(),
}


def current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user = db.scalar(select(User).where(User.email == payload["sub"], User.is_active.is_(True)))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def serialize_emergency(item: Emergency) -> dict[str, Any]:
    return {
        "id": item.id,
        "emergency_type": item.emergency_type.value,
        "location": item.location,
        "description": item.description,
        "status": item.status.value,
        "assigned_unit": item.assigned_unit_id,
        "facility": item.facility_id,
        "route": item.route or [],
        "alternative_route": item.alternative_route or [],
        "travel_cost": item.travel_cost,
        "created_at": item.created_at.isoformat(),
    }


def change_status(db: Session, item: Emergency, new_status: EmergencyStatus, user_id: int | None, note: str) -> None:
    if new_status not in TRANSITIONS[item.status]:
        raise HTTPException(status_code=409, detail=f"Invalid transition: {item.status.value} -> {new_status.value}")
    old_status = item.status
    item.status = new_status
    db.add(EmergencyHistory(
        emergency_id=item.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=user_id,
        note=note,
    ))


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "emergency-system"}


@router.get("/map")
def get_map(db: Session = Depends(get_db)) -> dict:
    seed_demo_data(db)
    roads = [{"source": road.source, "destination": road.destination, "weight": road.weight, "blocked": road.blocked} for road in db.scalars(select(Road))]
    data = graph_map_data(roads)
    facilities = [
        {"id": item.id, "name": item.name, "type": item.type.value, "node": item.node}
        for item in db.scalars(select(Facility).where(Facility.is_active.is_(True)))
    ]
    units = [
        {"id": item.id, "name": item.name, "type": item.type.value, "node": item.current_node, "status": item.status.value}
        for item in db.scalars(select(EmergencyUnit).where(EmergencyUnit.is_active.is_(True)))
    ]
    return {"nodes": list(data["nodes"]), "edges": list(data["edges"]), "facilities": facilities, "units": units}


@router.get("/facilities")
def list_facilities(db: Session = Depends(get_db)) -> list[dict]:
    seed_demo_data(db)
    return [
        {"id": f.id, "name": f.name, "type": f.type.value, "node": f.node, "status": "ACTIVE" if f.is_active else "INACTIVE", "is_demo": f.is_demo}
        for f in db.scalars(select(Facility).order_by(Facility.id))
    ]


@router.post("/facilities")
def create_facility(payload: FacilityCreate, _: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    facility = Facility(name=payload.name, type=FacilityType(payload.type), node=payload.node, is_active=payload.status == "ACTIVE", is_demo=False)
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return {"id": facility.id, "name": facility.name, "type": facility.type.value, "node": facility.node, "status": "ACTIVE" if facility.is_active else "INACTIVE"}


@router.patch("/facilities/{facility_id}")
def edit_facility(facility_id: int, payload: dict, _: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    facility = db.get(Facility, facility_id)
    if facility is None:
        raise HTTPException(404, "Facility not found")
    if "name" in payload:
        facility.name = payload["name"]
    if "node" in payload:
        facility.node = payload["node"]
    if "type" in payload:
        facility.type = FacilityType(payload["type"])
    if "status" in payload:
        facility.is_active = payload["status"] == "ACTIVE"
    db.commit()
    return {"id": facility.id, "name": facility.name, "type": facility.type.value, "node": facility.node, "status": "ACTIVE" if facility.is_active else "INACTIVE"}


@router.get("/units")
def list_units(db: Session = Depends(get_db)) -> list[dict]:
    seed_demo_data(db)
    return [
        {"id": u.id, "name": u.name, "type": u.type.value, "current_node": u.current_node, "status": u.status.value, "is_active": u.is_active, "is_demo": u.is_demo}
        for u in db.scalars(select(EmergencyUnit).order_by(EmergencyUnit.id))
    ]


@router.post("/units")
def create_unit(payload: EmergencyUnitCreate, _: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    data = payload.model_dump()
    data["type"] = UnitType(payload.type)
    data["status"] = UnitStatus(payload.status)
    unit = EmergencyUnit(**data, is_demo=False)
    db.add(unit)
    db.commit()
    return payload.model_dump()


@router.patch("/units/{unit_id}")
def edit_unit(unit_id: str, payload: dict, _: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    unit = db.get(EmergencyUnit, unit_id)
    if unit is None:
        raise HTTPException(404, "Unit not found")
    if unit.status == UnitStatus.DISPATCHED and payload.get("status") == "AVAILABLE":
        raise HTTPException(409, "Resolve or cancel the active assignment before making a dispatched unit available")
    if "name" in payload:
        unit.name = payload["name"]
    if "current_node" in payload:
        unit.current_node = payload["current_node"]
    if "type" in payload:
        unit.type = UnitType(payload["type"])
    if "status" in payload:
        unit.status = UnitStatus(payload["status"])
    if "is_active" in payload:
        unit.is_active = bool(payload["is_active"])
    db.commit()
    return {"id": unit.id, "name": unit.name, "type": unit.type.value, "current_node": unit.current_node, "status": unit.status.value}


@router.get("/emergencies")
def get_emergencies(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    query = select(Emergency).order_by(Emergency.created_at.desc())
    if user.role != UserRole.ADMIN:
        query = query.where(Emergency.reporter_id == user.id)
    return [serialize_emergency(item) for item in db.scalars(query)]


@router.post("/emergencies")
def emergency_create(payload: EmergencyCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    item = Emergency(
        reporter_id=user.id,
        emergency_type=EmergencyType(payload.emergency_type),
        location=payload.location,
        description=payload.description,
        status=EmergencyStatus.REPORTED,
    )
    db.add(item)
    db.flush()
    db.add(EmergencyHistory(emergency_id=item.id, old_status=None, new_status=EmergencyStatus.REPORTED, changed_by=user.id, note="Emergency reported"))
    db.commit()
    db.refresh(item)
    return serialize_emergency(item)


@router.get("/emergencies/{emergency_id}")
def get_emergency(emergency_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    item = db.get(Emergency, emergency_id)
    if item is None or (user.role != UserRole.ADMIN and item.reporter_id != user.id):
        raise HTTPException(404, "Emergency not found")
    return serialize_emergency(item)


def assign_emergency_record(db: Session, item: Emergency, actor_id: int) -> dict:
    if item.status not in {EmergencyStatus.REPORTED, EmergencyStatus.ASSIGNING}:
        raise HTTPException(409, "Emergency cannot be assigned in its current state")
    change_status(db, item, EmergencyStatus.ASSIGNING, actor_id, "Automatic assignment started")
    required_type = {
        EmergencyType.MEDICAL: UnitType.AMBULANCE,
        EmergencyType.FIRE: UnitType.FIRE_TRUCK,
        EmergencyType.CRIME: UnitType.POLICE_VEHICLE,
        EmergencyType.ACCIDENT: UnitType.AMBULANCE,
    }[item.emergency_type]
    units = list(db.scalars(select(EmergencyUnit).where(
        EmergencyUnit.type == required_type,
        EmergencyUnit.status == UnitStatus.AVAILABLE,
        EmergencyUnit.is_active.is_(True),
    )))
    roads = [{"source": road.source, "destination": road.destination, "weight": road.weight, "blocked": road.blocked} for road in db.scalars(select(Road))]
    distances = distances_from_source(item.location, roads)
    reachable = [(unit, distances[unit.current_node]) for unit in units if unit.current_node < len(distances) and distances[unit.current_node] != float("inf")]
    if not reachable:
        db.rollback()
        raise HTTPException(409, "No reachable available unit")
    unit, unit_cost = min(reachable, key=lambda value: value[1])
    facility_types = {EmergencyType.MEDICAL: {FacilityType.HOSPITAL}, EmergencyType.FIRE: {FacilityType.FIRE_STATION}, EmergencyType.CRIME: {FacilityType.POLICE_STATION}, EmergencyType.ACCIDENT: {FacilityType.HOSPITAL, FacilityType.POLICE_STATION}}[item.emergency_type]
    facilities = list(db.scalars(select(Facility).where(Facility.type.in_(facility_types), Facility.is_active.is_(True))))
    reachable_facilities = [(facility, distances[facility.node]) for facility in facilities if facility.node < len(distances) and distances[facility.node] != float("inf")]
    if not reachable_facilities:
        db.rollback()
        raise HTTPException(409, "No reachable active facility")
    facility = min(reachable_facilities, key=lambda value: value[1])[0]
    path = route(item.location, unit.current_node, roads)
    item.assigned_unit_id = unit.id
    item.facility_id = facility.id if facility else None
    item.route = path["route"]
    item.alternative_route = path["alternative_route"]
    item.travel_cost = unit_cost
    unit.status = UnitStatus.DISPATCHED
    db.add(Assignment(emergency_id=item.id, unit_id=unit.id, facility_id=item.facility_id, route=path["route"], travel_cost=unit_cost))
    change_status(db, item, EmergencyStatus.DISPATCHED, actor_id, "Unit and facility assigned")
    db.commit()
    return serialize_emergency(item)


@router.post("/emergencies/{emergency_id}/auto-assign")
def auto_assign(emergency_id: int, user: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    item = db.get(Emergency, emergency_id)
    if item is None:
        raise HTTPException(404, "Emergency not found")
    return assign_emergency_record(db, item, user.id)


@router.post("/emergencies/{emergency_id}/status/{new_status}")
def update_status(emergency_id: int, new_status: EmergencyStatus, user: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    item = db.get(Emergency, emergency_id)
    if item is None:
        raise HTTPException(404, "Emergency not found")
    change_status(db, item, new_status, user.id, f"Status changed to {new_status.value}")
    if new_status in {EmergencyStatus.RESOLVED, EmergencyStatus.CANCELLED} and item.assigned_unit_id:
        unit = db.get(EmergencyUnit, item.assigned_unit_id)
        if unit:
            unit.status = UnitStatus.AVAILABLE
        for assignment in db.scalars(select(Assignment).where(Assignment.emergency_id == item.id, Assignment.status == "ACTIVE")):
            assignment.status = "COMPLETED"
    db.commit()
    return serialize_emergency(item)


@router.post("/roads/block")
def block_road(payload: dict, _: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    road = db.scalar(select(Road).where(Road.source == payload["source"], Road.destination == payload["destination"]))
    if road is None:
        road = Road(source=payload["source"], destination=payload["destination"], weight=payload.get("weight", 1.0), blocked=True, is_demo=False)
        db.add(road)
    else:
        road.blocked = True
    db.commit()
    return {"status": "blocked", "source": road.source, "destination": road.destination}


@router.get("/roads")
def list_roads(_: User = Depends(admin_user), db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": road.id, "source": road.source, "destination": road.destination, "weight": road.weight, "blocked": road.blocked}
        for road in db.scalars(select(Road).order_by(Road.id))
    ]


@router.patch("/roads/{road_id}")
def edit_road(road_id: int, payload: dict, _: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    road = db.get(Road, road_id)
    if road is None:
        raise HTTPException(404, "Road not found")
    if "weight" in payload:
        if float(payload["weight"]) <= 0:
            raise HTTPException(422, "Road weight must be positive")
        road.weight = float(payload["weight"])
    if "blocked" in payload:
        road.blocked = bool(payload["blocked"])
    db.commit()
    return {"id": road.id, "source": road.source, "destination": road.destination, "weight": road.weight, "blocked": road.blocked}


@router.post("/roads/unblock")
def unblock_road(payload: dict, _: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    road = db.scalar(select(Road).where(Road.source == payload["source"], Road.destination == payload["destination"]))
    if road is None:
        raise HTTPException(404, "Road not found")
    road.blocked = False
    db.commit()
    return {"status": "unblocked"}


@router.post("/route")
def route_calculation(payload: RouteRequest, db: Session = Depends(get_db)) -> dict:
    roads = [{"source": road.source, "destination": road.destination, "weight": road.weight, "blocked": road.blocked} for road in db.scalars(select(Road))]
    if payload.source >= 36 or payload.destination >= 36:
        raise HTTPException(422, "Source and destination must be graph nodes from 0 through 35")
    result = route(payload.source, payload.destination, roads)
    if not result["success"]:
        raise HTTPException(409, "No route exists between the requested nodes")
    return {"route": result}


@router.post("/auth/register")
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "User already exists")
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=UserRole.USER)
    db.add(user)
    db.commit()
    token = create_access_token(user.email, user.role.value)
    return {"access_token": token, "token_type": "bearer", "role": user.role.value}


@router.post("/auth/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.email, user.role.value), role=user.role.value)


@router.get("/auth/current-user")
def read_current_user(user: User = Depends(current_user)) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role.value}
