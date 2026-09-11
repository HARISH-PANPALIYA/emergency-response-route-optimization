from typing import Literal

from pydantic import BaseModel, Field


class FacilityCreate(BaseModel):
    name: str = Field(..., min_length=2)
    type: Literal["HOSPITAL", "POLICE_STATION", "FIRE_STATION", "AMBULANCE_CENTER"]
    node: int = Field(..., ge=0)
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class FacilityRead(FacilityCreate):
    id: int
