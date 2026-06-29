import os
import requests
from typing import Dict, Any, Optional
from backend.services.base import BaseService
from backend.imaging_service import process_ct_scan
from backend.config import settings

class ImagingService(BaseService):
    """
    Service to handle 3D CT scan image processing, metadata extraction,
    nodule detection AI execution, and saving results.
    """

    def download_scan_file(self, file_url: str) -> str:
        """
        Downloads the CT scan file from a remote URL to the local uploads directory.
        """
        # Extract filename and strip query params if present
        local_filename = file_url.split("/")[-1].split("?")[0]
        file_path = os.path.join(settings.UPLOAD_DIR, local_filename)

        self.logger.info(f"Downloading scan from {file_url} to {file_path}")
        
        response = requests.get(file_url)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path

    def analyze_scan(self, scan_id: str, file_url: str, user_id: str) -> Dict[str, Any]:
        """
        Full workflow to download, process via AI model, save results,
        and update scan status in the database.
        """
        file_path = None
        try:
            # 1. Download the file
            file_path = self.download_scan_file(file_url)

            # 2. Run the CT Scan processing pipeline
            self.logger.info(f"Starting CT scan analysis pipeline for file: {file_path}")
            result = process_ct_scan(file_path)

            # 3. Format the result according to frontend schema
            structured_result = {
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "gradcam_base64": result.get("gradcam_base64"),
                "base_image_base64": result.get("base_image_base64"),
                "findings": [
                    f"Detection logic identified: {result['prediction']}",
                    "The image analysis has completed using the MedAI engine."
                ],
                "recommendations": [
                    "Review findings with a certified radiologist",
                    "Consider a follow-up scan based on the risk level"
                ],
                "risk_level": "high" if "malignant" in result["prediction"].lower() else "low"
            }

            # 4. Save results to Supabase database if available
            if self.supabase is not None:
                self.logger.info(f"Saving analysis results to database for scan_id: {scan_id}")
                
                # Insert results
                self.supabase.table("analysis_results").insert({
                    "scan_id": scan_id,
                    "user_id": user_id,
                    "result_data": structured_result
                }).execute()

                # Update scan status to completed
                self.supabase.table("scans").update({
                    "status": "completed"
                }).eq("id", scan_id).execute()

            return structured_result

        except Exception as e:
            self.logger.error(f"Error analyzing scan {scan_id}: {str(e)}", exc_info=True)
            # Mark scan as failed in database
            if self.supabase is not None:
                try:
                    self.supabase.table("scans").update({
                        "status": "failed"
                    }).eq("id", scan_id).execute()
                except Exception as db_err:
                    self.logger.error(f"Failed to update scan status to failed: {str(db_err)}")
            raise e
            
        finally:
            # Optional: Clean up local downloaded file if we don't want to store it long-term
            # if file_path and os.path.exists(file_path):
            #     os.remove(file_path)
            pass
            
    def get_scan_results(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the analysis results for a specific scan.
        """
        if self.supabase is None:
            return None
            
        response = self.supabase.table("analysis_results").select("*").eq("scan_id", scan_id).maybe_single().execute()
        return response.data if response else None
