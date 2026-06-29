"""
CT Scan Routing Module.

This module implements the endpoints for:
1. Uploading CT scan files (with type and size validation).
2. Running AI model predictions on uploaded scans.
3. Fetching user scan history with pagination.
4. Deleting scans and their associated database records and files.
5. Fetching scan stats and individual scan details (backwards compatible).
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from supabase import Client

from backend.config import settings
from backend.database import get_supabase
from backend.dependencies import get_current_user
from backend.schemas import (
    ScanPredictionResponse,
    ScanHistoryResponse,
    ScanUploadRequest
)
from backend.services.ai_service import AIService
from backend.services.storage_service import StorageService
from backend.utils.logger import get_logger

# Initialize logger for the scans router
logger = get_logger(__name__)

router = APIRouter(prefix="/scans", tags=["scans"])

# ==============================================================================
# Service Dependencies
# ==============================================================================

def get_storage_service(supabase_client: Client = Depends(get_supabase)) -> StorageService:
    """
    Dependency to retrieve the StorageService instance.
    """
    return StorageService(supabase_client=supabase_client)


def get_ai_service(supabase_client: Client = Depends(get_supabase)) -> AIService:
    """
    Dependency to retrieve the AIService instance.
    """
    return AIService(supabase_client=supabase_client)


# ==============================================================================
# Request/Response Schemas
# ==============================================================================

class PredictRequest(BaseModel):
    """
    Request schema for triggering AI prediction on an existing scan.
    """
    scan_id: str = Field(..., description="The unique ID of the scan to analyze")


# ==============================================================================
# Validation Helpers
# ==============================================================================

MAX_FILE_SIZE = 150 * 1024 * 1024  # 150 MB limit
ALLOWED_EXTENSIONS = (".nii", ".nii.gz", ".dcm")


def validate_scan_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is of an allowed type and within the size limit.
    """
    filename = file.filename or ""
    
    # 1. Validate file extension
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        logger.warning(f"Validation failed: Invalid file extension for file '{filename}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only NIfTI (.nii, .nii.gz) and DICOM (.dcm) files are supported."
        )
        
    # 2. Validate file size (if size is provided by Starlette)
    if file.size and file.size > MAX_FILE_SIZE:
        logger.warning(f"Validation failed: File size {file.size} exceeds maximum limit of 150MB")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum allowed size is 150MB."
        )


# ==============================================================================
# Route Handlers
# ==============================================================================

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_scan(
    file: UploadFile = File(...),
    scan_type: str = Form("CT"),
    notes: str = Form(""),
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase),
    storage_service: StorageService = Depends(get_storage_service),
    ai_service: AIService = Depends(get_ai_service)
) -> Dict[str, Any]:
    """
    Upload a new 3D CT scan.
    
    This endpoint:
    1. Validates the file extension and size.
    2. Saves the file locally and uploads it to Supabase Storage.
    3. Creates a 'pending' scan record in the database.
    4. Triggers AI inference and saves the analysis results (maintaining backwards compatibility).
    """
    logger.info(f"User {current_user.id} is uploading scan file: {file.filename}")
    
    # Validate file type and size
    validate_scan_file(file)
    
    # Read file content
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        logger.warning(f"Validation failed: Uploaded content length {len(file_content)} exceeds 150MB")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Maximum allowed size is 150MB."
        )
        
    try:
        # 1. Save file locally using StorageService
        local_path, unique_filename = storage_service.save_file_locally(file_content, file.filename)
        
        # 2. Upload to Supabase Storage
        file_ext = unique_filename.split(".")[-1]
        remote_filename = f"{uuid.uuid4()}.{file_ext}"
        storage_path = f"{current_user.id}/{remote_filename}"
        
        public_url = storage_service.upload_to_supabase(
            local_file_path=local_path,
            bucket_name="scans",
            destination_path=storage_path
        )
        
        if not public_url:
            logger.error("Failed to upload file to Supabase Storage.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store scan file in cloud storage."
            )
            
        # 3. Create scan record in Supabase database
        scan_record = supabase_client.table("scans").insert({
            "file_name": file.filename,
            "file_path": storage_path,
            "file_url": public_url,
            "scan_type": scan_type,
            "notes": notes,
            "status": "pending",
            "user_id": current_user.id
        }).execute()
        
        if not scan_record or not scan_record.data:
            logger.error("Failed to create scan record in database.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create scan record in database."
            )
            
        new_scan_id = scan_record.data[0]["id"]
        logger.info(f"Scan record created successfully. Scan ID: {new_scan_id}")
        
        # 4. Run AI Inference (to maintain backwards compatibility with frontend redirects)
        try:
            logger.info(f"Triggering automatic AI inference for scan ID: {new_scan_id}")
            ml_result = ai_service.run_ct_inference(local_path)
            
            structured_result = {
                "prediction": ml_result["prediction"],
                "confidence": ml_result["confidence"],
                "gradcam_base64": ml_result.get("gradcam_base64"),
                "base_image_base64": ml_result.get("base_image_base64"),
                "findings": [
                    f"Detection logic identified: {ml_result['prediction']}",
                    "The image analysis has completed using the MedAI engine."
                ],
                "recommendations": [
                    "Review findings with a certified radiologist",
                    "Consider a follow-up scan based on the risk level"
                ],
                "risk_level": "high" if "malignant" in ml_result["prediction"].lower() else "low"
            }
            
            # Save analysis results
            supabase_client.table("analysis_results").insert({
                "scan_id": new_scan_id,
                "user_id": current_user.id,
                "result_data": structured_result
            }).execute()
            
            # Update status to completed
            supabase_client.table("scans").update({"status": "completed"}).eq("id", new_scan_id).execute()
            logger.info(f"Automatic AI inference completed for scan ID: {new_scan_id}")
            
        except Exception as ai_err:
            logger.error(f"Automatic AI inference failed for scan ID {new_scan_id}: {ai_err}", exc_info=True)
            # Update status to failed
            supabase_client.table("scans").update({"status": "failed"}).eq("id", new_scan_id).execute()
            
        return {
            "status": "success",
            "scan_id": new_scan_id,
            "file_name": file.filename,
            "file_url": public_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed for {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )


@router.post("/predict", response_model=ScanPredictionResponse)
def predict_scan(
    req: PredictRequest,
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase),
    ai_service: AIService = Depends(get_ai_service),
    storage_service: StorageService = Depends(get_storage_service)
) -> ScanPredictionResponse:
    """
    Trigger AI prediction on an already uploaded CT scan.
    """
    logger.info(f"User {current_user.id} requested prediction on scan: {req.scan_id}")
    
    # 1. Fetch scan record from Supabase
    scan_resp = supabase_client.table("scans").select("*").eq("id", req.scan_id).eq("user_id", current_user.id).maybe_single().execute()
    if not scan_resp or not scan_resp.data:
        logger.warning(f"Scan ID {req.scan_id} not found for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
        
    scan_data = scan_resp.data
    local_filename = scan_data.get("file_name")
    local_path = os.path.join(settings.UPLOAD_DIR, local_filename)
    
    # Update status to processing
    supabase_client.table("scans").update({"status": "processing"}).eq("id", req.scan_id).execute()
    
    try:
        # 2. Check if local file exists, if not, we would download it (simplified here to local path check)
        if not os.path.exists(local_path):
            logger.error(f"Local scan file not found at {local_path} for inference.")
            raise FileNotFoundError("Local scan file has been cleaned up or is missing.")
            
        # 3. Run AI Inference
        ml_result = ai_service.run_ct_inference(local_path)
        
        structured_result = {
            "prediction": ml_result["prediction"],
            "confidence": ml_result["confidence"],
            "gradcam_base64": ml_result.get("gradcam_base64"),
            "base_image_base64": ml_result.get("base_image_base64"),
            "findings": [
                f"Detection logic identified: {ml_result['prediction']}",
                "The image analysis has completed using the MedAI engine."
            ],
            "recommendations": [
                "Review findings with a certified radiologist",
                "Consider a follow-up scan based on the risk level"
            ],
            "risk_level": "high" if "malignant" in ml_result["prediction"].lower() else "low"
        }
        
        # 4. Save/Update analysis results
        supabase_client.table("analysis_results").upsert({
            "scan_id": req.scan_id,
            "user_id": current_user.id,
            "result_data": structured_result
        }).execute()
        
        # 5. Update status to completed
        supabase_client.table("scans").update({"status": "completed"}).eq("id", req.scan_id).execute()
        
        # Parse created_at safely
        created_at_dt = scan_data.get("created_at")
        if not isinstance(created_at_dt, datetime):
            created_at_dt = datetime.fromisoformat(created_at_dt.replace("Z", "+00:00"))
            
        return ScanPredictionResponse(
            scan_id=req.scan_id,
            status="completed",
            prediction_class=ml_result["prediction"],
            probability=ml_result["confidence"],
            heatmap_url=ml_result.get("gradcam_base64"),
            created_at=created_at_dt
        )
        
    except Exception as e:
        logger.error(f"AI inference failed for scan ID {req.scan_id}: {e}", exc_info=True)
        supabase_client.table("scans").update({"status": "failed"}).eq("id", req.scan_id).execute()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )


@router.get("/history", response_model=List[ScanHistoryResponse])
def get_scan_history(
    limit: int = 10,
    offset: int = 0,
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase)
) -> List[ScanHistoryResponse]:
    """
    Retrieve the scan history of the authenticated user with pagination support.
    """
    logger.info(f"Fetching scan history for user {current_user.id} (limit={limit}, offset={offset})")
    
    try:
        # Query scans and join with analysis_results
        response = supabase_client.table("scans") \
            .select("*, analysis_results(*)") \
            .eq("user_id", current_user.id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
            
        history = []
        for item in response.data:
            prediction_data = None
            analysis_list = item.get("analysis_results", [])
            if analysis_list:
                analysis = analysis_list[0]
                result_data = analysis.get("result_data", {})
                
                # Parse analysis created_at safely
                analysis_created_at = analysis.get("created_at", item["created_at"])
                if not isinstance(analysis_created_at, datetime):
                    analysis_created_at = datetime.fromisoformat(analysis_created_at.replace("Z", "+00:00"))
                    
                prediction_data = ScanPredictionResponse(
                    scan_id=item["id"],
                    status=item["status"],
                    prediction_class=result_data.get("prediction"),
                    probability=result_data.get("confidence"),
                    heatmap_url=result_data.get("gradcam_base64"),
                    created_at=analysis_created_at
                )
                
            # Parse scan created_at safely
            scan_created_at = item["created_at"]
            if not isinstance(scan_created_at, datetime):
                scan_created_at = datetime.fromisoformat(scan_created_at.replace("Z", "+00:00"))
                
            history.append(ScanHistoryResponse(
                scan_id=item["id"],
                patient_id=item.get("patient_id") or item.get("user_id") or "N/A",
                status=item["status"],
                created_at=scan_created_at,
                prediction=prediction_data
            ))
            
        return history
        
    except Exception as e:
        logger.error(f"Failed to fetch scan history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan history: {str(e)}"
        )


@router.delete("/{scan_id}", status_code=status.HTTP_200_OK)
def delete_scan(
    scan_id: str,
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase),
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, str]:
    """
    Delete a scan, its local temporary files, and its database records.
    """
    logger.info(f"User {current_user.id} requested deletion of scan {scan_id}")
    
    # 1. Fetch scan record to get the file paths
    scan_resp = supabase_client.table("scans").select("*").eq("id", scan_id).eq("user_id", current_user.id).maybe_single().execute()
    if not scan_resp or not scan_resp.data:
        logger.warning(f"Scan {scan_id} not found for deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
        
    scan_data = scan_resp.data
    file_path = scan_data.get("file_path")
    local_filename = scan_data.get("file_name")
    
    # 2. Delete from Supabase Storage
    if file_path:
        try:
            supabase_client.storage.from_("scans").remove([file_path])
            logger.info(f"Deleted scan file from Supabase storage: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file from Supabase storage: {e}")
            
    # 3. Delete local temporary file
    if local_filename:
        local_path = os.path.join(settings.UPLOAD_DIR, local_filename)
        storage_service.delete_file(local_path)
        
    # 4. Delete database records (cascade deleting analysis_results and reports)
    try:
        supabase_client.table("analysis_results").delete().eq("scan_id", scan_id).execute()
        supabase_client.table("reports").delete().eq("scan_id", scan_id).execute()
        supabase_client.table("scans").delete().eq("id", scan_id).execute()
        logger.info(f"Successfully deleted database records for scan ID: {scan_id}")
        return {"status": "success", "message": "Scan deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete database records: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database deletion failed: {str(e)}"
        )


# ==============================================================================
# Backwards Compatibility Routes
# ==============================================================================

@router.get("/")
def get_scans(
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase)
) -> Dict[str, Any]:
    """
    Legacy endpoint to get all scans of the current user.
    """
    logger.info(f"Fetching all scans for user {current_user.id}")
    try:
        response = supabase_client.table("scans").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
        return {"scans": response.data}
    except Exception as e:
        logger.error(f"Failed to retrieve scans: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats")
def get_stats(
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase)
) -> Dict[str, int]:
    """
    Legacy endpoint to fetch scan count statistics.
    """
    logger.info(f"Fetching scan stats for user {current_user.id}")
    try:
        total = supabase_client.table("scans").select("*", count="exact").eq("user_id", current_user.id).execute()
        analyzed = supabase_client.table("scans").select("*", count="exact").eq("user_id", current_user.id).eq("status", "completed").execute()
        return {
            "total_scans": total.count if (total and hasattr(total, "count")) else 0,
            "analyzed_scans": analyzed.count if (analyzed and hasattr(analyzed, "count")) else 0
        }
    except Exception as e:
        logger.error(f"Failed to retrieve scan stats: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{scan_id}")
def get_scan(
    scan_id: str,
    current_user = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase)
) -> Dict[str, Any]:
    """
    Legacy endpoint to fetch details of a specific scan and its analysis results.
    """
    logger.info(f"Fetching details for scan ID: {scan_id}")
    try:
        scan_response = supabase_client.table("scans").select("*").eq("id", scan_id).eq("user_id", current_user.id).maybe_single().execute()
        if not scan_response or not scan_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
            
        result_response = supabase_client.table("analysis_results").select("*").eq("scan_id", scan_id).maybe_single().execute()
        
        return {
            "scan": scan_response.data,
            "result": result_response.data if result_response and result_response.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve scan: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
