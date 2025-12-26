from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List, Dict, Any
from collections import defaultdict

from models.database import get_db
from models.rescue_report import RescueReport
from services.validator import ReportValidator
from schemas.report_schemas import DashboardResponse, IncidentSummary, ReportResponse

router = APIRouter(prefix="/admin", tags=["admin"])
validator = ReportValidator()

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: Session = Depends(get_db)):
    """Get NGO dashboard with verified and clustered reports"""
    try:
        # Get all verified reports
        verified_reports_query = select(RescueReport).where(RescueReport.is_verified == True)
        verified_reports = db.exec(verified_reports_query).all()
        
        # Get all reports for statistics
        all_reports = db.exec(select(RescueReport)).all()
        
        if not verified_reports:
            return DashboardResponse(
                incidents=[],
                total_reports=len(all_reports),
                total_incidents=0,
                verified_reports=0,
                pending_verification=len(all_reports)
            )
        
        # Cluster verified reports
        clustered_reports = validator.cluster_reports_by_location(verified_reports)
        
        # Create incident summaries
        incidents = []
        for incident_id, incident_reports in clustered_reports.items():
            # Calculate aggregated data for the incident
            priorities = [r.priority for r in incident_reports]
            disaster_types = list(set([r.disaster_type for r in incident_reports]))
            
            # Calculate center location
            avg_lat = sum(r.location_lat for r in incident_reports) / len(incident_reports)
            avg_lng = sum(r.location_lng for r in incident_reports) / len(incident_reports)
            
            incident = IncidentSummary(
                incident_id=incident_id,
                total_reports=len(incident_reports),
                authentic_reports=len(incident_reports),  # All verified reports are considered authentic
                priority=max(priorities) if priorities else 1,
                disaster_types=disaster_types,
                location={"lat": avg_lat, "lng": avg_lng},
                reports=[ReportResponse.from_orm(report) for report in incident_reports]
            )
            incidents.append(incident)
        
        # Sort incidents by priority (descending) and then by timestamp
        incidents.sort(key=lambda x: (-x.priority, max(r.timestamp for r in x.reports)))
        
        # Calculate statistics
        total_verified = len(verified_reports)
        total_pending = len([r for r in all_reports if not r.is_verified])
        
        return DashboardResponse(
            incidents=incidents,
            total_reports=len(all_reports),
            total_incidents=len(incidents),
            verified_reports=total_verified,
            pending_verification=total_pending
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard: {str(e)}"
        )

@router.get("/incidents/{incident_id}", response_model=IncidentSummary)
async def get_incident_details(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific incident"""
    try:
        # Get all reports for this incident
        reports_query = select(RescueReport).where(
            RescueReport.incident_id == incident_id,
            RescueReport.is_verified == True
        )
        incident_reports = db.exec(reports_query).all()
        
        if not incident_reports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Calculate incident summary
        priorities = [r.priority for r in incident_reports]
        disaster_types = list(set([r.disaster_type for r in incident_reports]))
        
        # Calculate center location
        avg_lat = sum(r.location_lat for r in incident_reports) / len(incident_reports)
        avg_lng = sum(r.location_lng for r in incident_reports) / len(incident_reports)
        
        return IncidentSummary(
            incident_id=incident_id,
            total_reports=len(incident_reports),
            authentic_reports=len(incident_reports),
            priority=max(priorities) if priorities else 1,
            disaster_types=disaster_types,
            location={"lat": avg_lat, "lng": avg_lng},
            reports=[ReportResponse.from_orm(report) for report in incident_reports]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch incident details: {str(e)}"
        )

@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall statistics for the platform"""
    try:
        # Basic counts
        total_reports = len(db.exec(select(RescueReport)).all())
        verified_reports = len(db.exec(select(RescueReport).where(RescueReport.is_verified == True)).all())
        
        # Disaster type breakdown
        disaster_type_counts = db.exec(
            select(RescueReport.disaster_type, func.count(RescueReport.id))
            .group_by(RescueReport.disaster_type)
        ).all()
        
        # Priority breakdown
        priority_counts = db.exec(
            select(RescueReport.priority, func.count(RescueReport.id))
            .where(RescueReport.is_verified == True)
            .group_by(RescueReport.priority)
        ).all()
        
        # Recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_reports = len(db.exec(
            select(RescueReport).where(RescueReport.timestamp >= yesterday)
        ).all())
        
        return {
            "total_reports": total_reports,
            "verified_reports": verified_reports,
            "pending_verification": total_reports - verified_reports,
            "verification_rate": (verified_reports / total_reports * 100) if total_reports > 0 else 0,
            "disaster_type_breakdown": dict(disaster_type_counts),
            "priority_breakdown": dict(priority_counts),
            "recent_reports_24h": recent_reports
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )
