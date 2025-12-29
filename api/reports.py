from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime

from models.database import get_db
from models.rescue_report import RescueReport, RescueReportCreate
from ML.services.validator import ReportValidator
from schemas.report_schemas import (
    ReportSubmitRequest,
    BatchSyncRequest,
    ReportResponse,
    BatchSyncResponse,
    DashboardResponse,
    IncidentSummary
)

router = APIRouter(prefix="/reports", tags=["reports"])
validator = ReportValidator()

@router.post("/submit", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    report_data: ReportSubmitRequest,
    db: Session = Depends(get_db)
):
    """Submit a single disaster report"""
    try:
        # Create report model
        report = RescueReport(
            location_lat=report_data.location_lat,
            location_lng=report_data.location_lng,
            disaster_type=report_data.disaster_type,
            needs=report_data.needs,
            priority=report_data.priority,
            title=report_data.title,
            description=report_data.description
        )
        
        validation_result = validator.validate_report_authenticity(report)
        
        if validation_result["is_likely_authentic"]:
            report.is_verified = True
        
        db.add(report)
        db.commit()
        db.refresh(report)
        return ReportResponse.from_orm(report)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit report: {str(e)}"
        )

@router.post("/sync", response_model=BatchSyncResponse)
async def sync_batch_reports(
    batch_data: BatchSyncRequest,
    db: Session = Depends(get_db)
):
    """Sync multiple reports for offline-first functionality"""
    try:
        created_reports = []
        # Process each report in the batch
        for report_data in batch_data.reports:
            report = RescueReport(
                location_lat=report_data.location_lat,
                location_lng=report_data.location_lng,
                disaster_type=report_data.disaster_type,
                needs=report_data.needs,
                priority=report_data.priority,
                title=report_data.title,
                description=report_data.description
            )
            # Validate report authenticity
            validation_result = validator.validate_report_authenticity(report)
            if validation_result["is_likely_authentic"]:
                report.is_verified = True
            
            db.add(report)
            created_reports.append(report)
        db.commit()
        
        for report in created_reports:
            db.refresh(report)

        batch_result = validator.process_batch_reports(created_reports)
        
        # Update incident IDs for clustered reports
        for incident_id, incident_reports in batch_result["clustered_reports"].items():
            for report in incident_reports:
                report.incident_id = incident_id
                db.add(report)
        db.commit()
        
        return BatchSyncResponse(
            success=True,
            message=f"Successfully processed {len(created_reports)} reports into {len(batch_result['clustered_reports'])} incidents",
            processed_reports=len(created_reports),
            incidents_created=len(batch_result["clustered_reports"]),
            reports_with_ids=[{"id": r.id, "incident_id": r.incident_id} for r in created_reports]
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync reports: {str(e)}"
        )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific report by ID"""
    try:
        report = db.get(RescueReport, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        return ReportResponse.from_orm(report)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch report: {str(e)}"
        )