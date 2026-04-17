from fastapi import APIRouter, HTTPException, Depends
from backend.supabase_client import supabase
from backend.routes.auth import get_current_user
from typing import Optional

router = APIRouter(prefix="/scans", tags=["scans"])

@router.get("/")
def get_scans(user = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    try:
        response = supabase.table("scans").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        return {"scans": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{scan_id}")
def get_scan(scan_id: str, user = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    try:
        scan_response = supabase.table("scans").select("*").eq("id", scan_id).eq("user_id", user.id).maybe_single().execute()
        if not scan_response or not scan_response.data:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        result_response = supabase.table("analysis_results").select("*").eq("scan_id", scan_id).maybe_single().execute()
        
        return {
            "scan": scan_response.data,
            "result": result_response.data if result_response and result_response.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats")
def get_stats(user = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    try:
        total = supabase.table("scans").select("id", count="exact").eq("user_id", user.id).execute()
        analyzed = supabase.table("scans").select("id", count="exact").eq("user_id", user.id).eq("status", "completed").execute()
        return {
            "total_scans": total.count if total else 0,
            "analyzed_scans": analyzed.count if analyzed else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi import UploadFile, File, Form
import os
import shutil
import uuid
from backend.imaging_service import process_ct_scan

@router.post("/upload")
async def upload_scan(
    file: UploadFile = File(...),
    scan_type: str = Form("2d"),
    notes: str = Form(""),
    user = Depends(get_current_user)
):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")

    # Save locally to process
    UPLOAD_DIR = "data/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Read for supabase upload
        with open(temp_path, "rb") as f:
            file_bytes = f.read()

        file_ext = file.filename.split(".")[-1]
        remote_filename = f"{uuid.uuid4()}.{file_ext}"
        storage_path = f"{user.id}/{remote_filename}"
        
        # Upload to Supabase Storage
        res = supabase.storage.from_("scans").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        
        public_url = supabase.storage.from_("scans").get_public_url(storage_path)

        # Create scan record
        scan_record = supabase.table("scans").insert({
            "file_name": file.filename,
            "file_path": storage_path,
            "file_url": public_url,
            "scan_type": scan_type,
            "notes": notes,
            "status": "pending",
            "user_id": user.id
        }).execute()

        new_scan_id = scan_record.data[0]["id"]

        # Process the CT scan
        ml_result = process_ct_scan(temp_path)

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

        # Save analysis
        supabase.table("analysis_results").insert({
            "scan_id": new_scan_id,
            "user_id": user.id,
            "result_data": structured_result
        }).execute()

        # Mark completed
        supabase.table("scans").update({"status": "completed"}).eq("id", new_scan_id).execute()

        return {"status": "success", "scan_id": new_scan_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

