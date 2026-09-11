from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db import EmergencyUnit, Facility, FacilityType, Road, UnitStatus, UnitType, User, UserRole


FACILITIES = [
    ("Central Government Hospital", FacilityType.HOSPITAL, 5),
    ("District General Hospital", FacilityType.HOSPITAL, 12),
    ("Government Trauma Centre", FacilityType.HOSPITAL, 18),
    ("Central Police Station", FacilityType.POLICE_STATION, 22),
    ("East Police Station", FacilityType.POLICE_STATION, 28),
    ("West Police Station", FacilityType.POLICE_STATION, 31),
    ("Central Fire Station", FacilityType.FIRE_STATION, 8),
    ("North Fire Station", FacilityType.FIRE_STATION, 15),
    ("Industrial Fire Station", FacilityType.FIRE_STATION, 25),
    ("Central Ambulance Centre", FacilityType.AMBULANCE_CENTER, 17),
    ("District Ambulance Centre", FacilityType.AMBULANCE_CENTER, 27),
]

UNITS = [
    ("AMBULANCE-A01", UnitType.AMBULANCE, 4),
    ("AMBULANCE-A02", UnitType.AMBULANCE, 17),
    ("AMBULANCE-A03", UnitType.AMBULANCE, 23),
    ("FIRE-F01", UnitType.FIRE_TRUCK, 7),
    ("FIRE-F02", UnitType.FIRE_TRUCK, 14),
    ("POLICE-P01", UnitType.POLICE_VEHICLE, 3),
    ("POLICE-P02", UnitType.POLICE_VEHICLE, 25),
]


def seed_demo_data(db: Session) -> None:
    settings = get_settings()
    admin_email = getattr(settings, "admin_email", None)
    admin_password = getattr(settings, "admin_password", None)
    if admin_email and admin_password and db.scalar(select(User).where(User.email == admin_email)) is None:
        db.add(User(email=admin_email, password_hash=hash_password(admin_password), role=UserRole.ADMIN))
    existing_facilities = {name for name in db.scalars(select(Facility.name))}
    db.add_all([
        Facility(name=name, type=facility_type, node=node, is_demo=True)
        for name, facility_type, node in FACILITIES
        if name not in existing_facilities
    ])
    for unit_id, unit_type, node in UNITS:
        if db.get(EmergencyUnit, unit_id) is None:
            db.add(EmergencyUnit(
                id=unit_id,
                name=unit_id,
                type=unit_type,
                current_node=node,
                status=UnitStatus.AVAILABLE,
                is_demo=True,
            ))
    existing_roads = {(road.source, road.destination) for road in db.scalars(select(Road))}
    # Road persistence mirrors the synthetic C++ graph's base grid edges.
    expected_roads = []
    for source in range(36):
        row, column = divmod(source, 6)
        candidates = []
        if column + 1 < 6:
            candidates.append((source + 1, 4.0))
        if row + 1 < 6:
            candidates.append((source + 6, 5.0))
        if column + 1 < 6 and row + 1 < 6:
            candidates.append((source + 7, 6.0))
        if column > 0 and row + 1 < 6:
            candidates.append((source + 5, 6.0))
        expected_roads.extend((source, destination, weight) for destination, weight in candidates)
    expected_roads.extend([(2, 20, 8.5), (10, 29, 7.5), (13, 33, 9.0), (21, 12, 8.0)])
    db.add_all([
        Road(source=source, destination=destination, weight=weight, is_demo=True)
        for source, destination, weight in expected_roads
        if (source, destination) not in existing_roads
    ])
    db.commit()
