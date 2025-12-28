from sqlmodel import SQLModel, Field, Column, String, Float, Integer, DateTime, Boolean, Text, JSON
from datetime import datetime
from typing import List, Optional

class RescueReportBase(SQLModel):
    location_lat: float = Field(index=True)
    location_lng: float = Field(index=True)
    disaster_type: str = Field(max_length=100)
    needs: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    priority: int = Field(ge=1, le=5)
    title: str = Field(max_length=200, nullable=False)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_verified: bool = Field(default=False)
    incident_id: Optional[str] = Field(default=None, max_length=50)

class RescueReport(RescueReportBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "location_lat": 40.7128,
                "location_lng": -74.0060,
                "disaster_type": "flood",
                "needs": ["food", "water", "medical"],
                "priority": 5,
                "title": "Flood in downtown area",
                "description": "Multiple buildings flooded, people trapped",
                "is_verified": False,
                "incident_id": None,
                "timestamp": "2023-12-25T11:43:00"
            }
        }

class RescueReportCreate(RescueReportBase):
    pass

class RescueReportRead(RescueReportBase):
    id: int
    timestamp: datetime

class RescueReportUpdate(SQLModel):
    is_verified: Optional[bool] = None
    incident_id: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
