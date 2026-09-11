from typing import Literal

from pydantic import BaseModel, Field


class EmergencyUnitCreate(BaseModel):
    id: str = Field(..., min_length=3)
    name: str = Field(..., min_length=2)
    type: Literal["AMBULANCE", "FIRE_TRUCK", "POLICE_VEHICLE"]
    current_node: int = Field(..., ge=0)
    status: Literal["AVAILABLE", "DISPATCHED", "BUSY", "OFFLINE"] = "AVAILABLE"


class EmergencyUnitRead(EmergencyUnitCreate):
    pass
