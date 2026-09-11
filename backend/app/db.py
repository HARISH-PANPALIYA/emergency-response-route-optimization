from collections.abc import Generator
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class FacilityType(str, Enum):
    HOSPITAL = "HOSPITAL"
    POLICE_STATION = "POLICE_STATION"
    FIRE_STATION = "FIRE_STATION"
    AMBULANCE_CENTER = "AMBULANCE_CENTER"


class UnitType(str, Enum):
    AMBULANCE = "AMBULANCE"
    FIRE_TRUCK = "FIRE_TRUCK"
    POLICE_VEHICLE = "POLICE_VEHICLE"


class UnitStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DISPATCHED = "DISPATCHED"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"


class EmergencyType(str, Enum):
    MEDICAL = "MEDICAL"
    FIRE = "FIRE"
    CRIME = "CRIME"
    ACCIDENT = "ACCIDENT"


class EmergencyStatus(str, Enum):
    REPORTED = "REPORTED"
    ASSIGNING = "ASSIGNING"
    DISPATCHED = "DISPATCHED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Facility(Base):
    __tablename__ = "facilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[FacilityType] = mapped_column(SqlEnum(FacilityType))
    node: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class EmergencyUnit(Base):
    __tablename__ = "emergency_units"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[UnitType] = mapped_column(SqlEnum(UnitType))
    current_node: Mapped[int] = mapped_column(Integer)
    status: Mapped[UnitStatus] = mapped_column(SqlEnum(UnitStatus), default=UnitStatus.AVAILABLE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Road(Base):
    __tablename__ = "roads"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[int] = mapped_column(Integer)
    destination: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Emergency(Base):
    __tablename__ = "emergencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    emergency_type: Mapped[EmergencyType] = mapped_column(SqlEnum(EmergencyType))
    location: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[EmergencyStatus] = mapped_column(SqlEnum(EmergencyStatus), default=EmergencyStatus.REPORTED)
    assigned_unit_id: Mapped[Optional[str]] = mapped_column(ForeignKey("emergency_units.id"), nullable=True)
    facility_id: Mapped[Optional[int]] = mapped_column(ForeignKey("facilities.id"), nullable=True)
    route: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    alternative_route: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    travel_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    emergency_id: Mapped[int] = mapped_column(ForeignKey("emergencies.id"))
    unit_id: Mapped[str] = mapped_column(ForeignKey("emergency_units.id"))
    facility_id: Mapped[Optional[int]] = mapped_column(ForeignKey("facilities.id"), nullable=True)
    route: Mapped[list] = mapped_column(JSON)
    travel_cost: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EmergencyHistory(Base):
    __tablename__ = "emergency_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    emergency_id: Mapped[int] = mapped_column(ForeignKey("emergencies.id"))
    old_status: Mapped[Optional[EmergencyStatus]] = mapped_column(SqlEnum(EmergencyStatus), nullable=True)
    new_status: Mapped[EmergencyStatus] = mapped_column(SqlEnum(EmergencyStatus))
    changed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def _engine_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(_engine_url(get_settings().database_url), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
