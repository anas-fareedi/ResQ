from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ReportSubmitRequest(BaseModel):
    location_lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    location_lng: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    disaster_type: str = Field(..., min_length=1, max_length=100)
    needs: List[str] = Field(default_factory=list, description="List of immediate needs")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5, 5 being highest)")
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "location_lat": 40.7128,
                "location_lng": -74.0060,
                "disaster_type": "flood",
                "needs": ["food", "water", "medical"],
                "priority": 5,
                "title": "Flood in downtown area",
                "description": "Multiple buildings flooded, people trapped"
            }
        }

class BatchSyncRequest(BaseModel):
    reports: List[ReportSubmitRequest] = Field(..., min_items=1, max_items=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "reports": [
                    {
                        "location_lat": 40.7128,
                        "location_lng": -74.0060,
                        "disaster_type": "flood",
                        "needs": ["food", "water"],
                        "priority": 5,
                        "title": "Flood near main street"
                    }
                ]
            }
        }

class ReportResponse(BaseModel):
    id: int
    location_lat: float
    location_lng: float
    disaster_type: str
    needs: List[str]
    priority: int
    title: str
    description: Optional[str]
    is_verified: bool
    incident_id: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class IncidentSummary(BaseModel):
    incident_id: str
    total_reports: int
    authentic_reports: int
    priority: int
    disaster_types: List[str]
    location: Dict[str, float]
    reports: List[ReportResponse]

class DashboardResponse(BaseModel):
    incidents: List[IncidentSummary]
    total_reports: int
    total_incidents: int
    verified_reports: int
    pending_verification: int

class BatchSyncResponse(BaseModel):
    success: bool
    message: str
    processed_reports: int
    incidents_created: int
    reports_with_ids: List[Dict[str, Any]]

class ValidationResponse(BaseModel):
    is_likely_authentic: bool
    similarity_score: float
    matching_news: Optional[str]
    fake_indicators: List[bool]
    fake_score: float

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
