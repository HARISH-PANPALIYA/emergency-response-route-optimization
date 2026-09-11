from typing import Literal, Optional

from pydantic import BaseModel, Field


class EmergencyCreate(BaseModel):
    emergency_type: Literal["MEDICAL", "FIRE", "CRIME", "ACCIDENT"]
    location: int = Field(..., ge=0)
    description: str = Field(..., min_length=5, max_length=1000)


class EmergencyRead(EmergencyCreate):
    id: int
    status: str = "REPORTED"
    assigned_unit: Optional[str] = None
    facility: Optional[str] = None
    route: list[int] = []
    travel_cost: Optional[float] = None


class RouteRequest(BaseModel):
    source: int = Field(..., ge=0)
    destination: int = Field(..., ge=0)
