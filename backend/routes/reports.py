"""
Medical Reports Routing Module.

This module implements the endpoints for:
1. Fetching report details or creating a ReportResponse by Scan ID.
2. Generating structured medical reports (both by Scan ID path parameter and request body).
3. Retrieving report history with pagination.
4. Downloading HTML reports.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from supabase import Client

from backend.config import settings
from backend.database import get_supabase
from backend.dependencies import get_current_user
from backend.schemas import ReportResponse, GenerateReportRequest
from backend.services.report_service import ReportService
from backend.utils.logger import get_logger

# Initialize logger for the reports router
logger = get_logger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_service(supabase_client: Client = Depends(get_supabase)) -> ReportService:
    """
    Dependency to retrieve the ReportService instance.
    """
    return ReportService(supabase_client=supabase_client)


# ==============================================================================
# Route Handlers
# ==============================================================================

@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_report(
    req: GenerateReportRequest,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase),
    service: ReportService = Depends(get_report_service)
) -> Dict[str, Any]:
    """
    Legacy endpoint to generate a report (accepts scan_id in request body).
    """
    logger.info(f"Generating report (legacy) for scan ID: {req.scan_id}")
    
    # 1. Fetch analysis results for the scan
    analysis_resp = supabase.table("analysis_results").select("*").eq("scan_id", req.scan_id).maybe_single().execute()
    if not analysis_resp or not analysis_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No analysis results found for scan: {req.scan_id}. Please run analysis first."
        )

    analysis_data = analysis_resp.data.get("result_data", {})
    
    # 2. Generate HTML report content
    html_content = service.generate_html_report(
        scan_id=req.scan_id,
        analysis_data=analysis_data,
        patient_email=req.patient_email
    )

    # 3. Save report and record metadata
    title = f"MedAI CT Scan Analysis Report - Scan {req.scan_id[:8]}"
    summary = f"AI classification: {analysis_data.get('prediction', 'N/A')} with {analysis_data.get('confidence', 0.0)*100:.1f}% confidence."
    
    report_metadata = service.save_report(
        scan_id=req.scan_id,
        user_id=current_user.id,
        title=title,
        summary=summary,
        html_content=html_content
    )

    return {
        "status": "success",
        "data": report_metadata
    }


@router.post("/generate/{scan_id}", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report_by_scan_id(
    scan_id: str,
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase),
    report_service: ReportService = Depends(get_report_service)
) -> ReportResponse:
    """
    Generate a structured medical report for a specific scan ID.
    """
    logger.info(f"Generating report for scan ID: {scan_id}")
    
    # 1. Fetch scan metadata
    scan_resp = supabase_client.table("scans").select("*").eq("id", scan_id).eq("user_id", current_user.id).maybe_single().execute()
    if not scan_resp or not scan_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    scan_data = scan_resp.data
    
    # 2. Fetch analysis results
    analysis_resp = supabase_client.table("analysis_results").select("*").eq("scan_id", scan_id).maybe_single().execute()
    if not analysis_resp or not analysis_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Analysis results not found. Please run prediction first."
        )
    analysis_data = analysis_resp.data.get("result_data", {})
    
    # 3. Generate HTML report content
    html_content = report_service.generate_html_report(
        scan_id=scan_id,
        analysis_data=analysis_data,
        patient_email=current_user.email
    )
    
    # 4. Save report and record metadata
    title = f"MedAI CT Scan Analysis Report - Scan {scan_id[:8]}"
    summary = f"AI classification: {analysis_data.get('prediction', 'N/A')} with {analysis_data.get('confidence', 0.0)*100:.1f}% confidence."
    
    report_metadata = report_service.save_report(
        scan_id=scan_id,
        user_id=current_user.id,
        title=title,
        summary=summary,
        html_content=html_content
    )
    
    created_at_dt = report_metadata.get("created_at")
    if not isinstance(created_at_dt, datetime):
        created_at_dt = datetime.fromisoformat(created_at_dt.replace("Z", "+00:00"))
        
    return ReportResponse(
        id=report_metadata["id"],
        scan_id=scan_id,
        patient_id=scan_data.get("patient_id") or current_user.id,
        report_text=summary,
        generated_by="MedAI-3D-System",
        created_at=created_at_dt
    )


@router.get("/history", response_model=List[ReportResponse])
def get_reports_history(
    limit: int = 10,
    offset: int = 0,
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase)
) -> List[ReportResponse]:
    """
    List previous reports generated for the authenticated user with pagination support.
    """
    logger.info(f"Fetching reports history for user {current_user.id} (limit={limit}, offset={offset})")
    
    try:
        response = supabase_client.table("reports") \
            .select("*") \
            .eq("user_id", current_user.id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
            
        reports = []
        for item in response.data:
            created_at_dt = item["created_at"]
            if not isinstance(created_at_dt, datetime):
                created_at_dt = datetime.fromisoformat(created_at_dt.replace("Z", "+00:00"))
                
            reports.append(ReportResponse(
                id=item["id"],
                scan_id=item["scan_id"],
                patient_id=current_user.id,
                report_text=item.get("summary") or item.get("title") or "N/A",
                generated_by="MedAI-3D-System",
                created_at=created_at_dt
            ))
        return reports
    except Exception as e:
        logger.error(f"Failed to fetch reports history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports history: {str(e)}"
        )


@router.get("/{id}")
def get_report_by_id_or_scan_id(
    id: str,
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase),
    report_service: ReportService = Depends(get_report_service)
) -> Any:
    """
    Fetch report details.
    
    Supports fetching:
    1. By Report ID (for backwards compatibility, returning raw metadata).
    2. By Scan ID (returns a structured ReportResponse).
    """
    logger.info(f"Fetching report/scan details for ID: {id}")
    
    # 1. Try to fetch as a Report ID first
    try:
        report = report_service.get_report_by_id(id)
        if report:
            if report.get("user_id") != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this report")
            return report
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"ID {id} is not a valid report ID or query failed: {e}")
        
    # 2. Fallback to fetching by Scan ID (returns ReportResponse)
    try:
        # Fetch scan metadata
        scan_resp = supabase_client.table("scans").select("*").eq("id", id).eq("user_id", current_user.id).maybe_single().execute()
        if not scan_resp or not scan_resp.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report or Scan not found")
        scan_data = scan_resp.data
        
        # Fetch analysis results
        analysis_resp = supabase_client.table("analysis_results").select("*").eq("scan_id", id).maybe_single().execute()
        if not analysis_resp or not analysis_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Analysis results not found for this scan. Please run prediction first."
            )
        analysis_data = analysis_resp.data
        result_data = analysis_data.get("result_data", {})
        
        # Check if report record exists
        report_resp = supabase_client.table("reports").select("*").eq("scan_id", id).maybe_single().execute()
        
        report_id = str(uuid.uuid4())
        report_text = f"AI Classification: {result_data.get('prediction', 'N/A')}. Confidence: {result_data.get('confidence', 0.0)*100:.2f}%."
        generated_by = "MedAI-3D-System"
        
        # Parse scan created_at safely
        created_at_dt = scan_data["created_at"]
        if not isinstance(created_at_dt, datetime):
            created_at_dt = datetime.fromisoformat(created_at_dt.replace("Z", "+00:00"))
        
        if report_resp and report_resp.data:
            report_record = report_resp.data
            report_id = report_record.get("id", report_id)
            report_text = report_record.get("summary", report_text)
            
            # Parse report created_at safely
            created_at_dt = report_record["created_at"]
            if not isinstance(created_at_dt, datetime):
                created_at_dt = datetime.fromisoformat(created_at_dt.replace("Z", "+00:00"))
            
        return ReportResponse(
            id=report_id,
            scan_id=id,
            patient_id=scan_data.get("patient_id") or current_user.id,
            report_text=report_text,
            generated_by=generated_by,
            created_at=created_at_dt
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve report or scan for ID {id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/download/{report_id}", response_class=HTMLResponse)
def download_report(
    report_id: str,
    service: ReportService = Depends(get_report_service)
) -> HTMLResponse:
    """
    Renders/downloads the generated HTML report file.
    """
    logger.info(f"Downloading HTML report for report ID: {report_id}")
    
    report = service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        
    # Locate the saved HTML report file
    file_path = os.path.join(settings.OUTPUT_FOLDER, f"report_{report_id}.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found on disk")
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return HTMLResponse(content=content)
