import os
from typing import Dict, Any, Optional, Tuple
from backend.services.base import BaseService
from backend.config import settings
from backend.utils.helpers import get_safe_filename

class StorageService(BaseService):
    """
    Service to manage file uploads, downloads, and storage buckets (Local and Supabase).
    """

    def save_file_locally(self, file_content: bytes, original_filename: str) -> Tuple[str, str]:
        """
        Saves raw file content to the local upload directory with a secure, unique name.
        Returns a tuple of (file_path, unique_filename).
        """
        unique_filename = get_safe_filename(original_filename)
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        self.logger.info(f"Saving file locally: {file_path}")
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        return file_path, unique_filename

    def upload_to_supabase(self, local_file_path: str, bucket_name: str, destination_path: str) -> Optional[str]:
        """
        Uploads a local file to a Supabase Storage bucket.
        Returns the public URL of the uploaded file, or None if it fails.
        """
        if not self.supabase:
            self.logger.warning("Supabase client is not initialized. Cannot upload file.")
            return None

        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found for upload: {local_file_path}")

        try:
            self.logger.info(f"Uploading {local_file_path} to Supabase bucket '{bucket_name}' path '{destination_path}'")
            
            with open(local_file_path, 'rb') as f:
                self.supabase.storage.from_(bucket_name).upload(
                    path=destination_path,
                    file=f,
                    file_options={"cache-control": "3600", "upsert": "true"}
                )
                
            # Retrieve the public URL
            response = self.supabase.storage.from_(bucket_name).get_public_url(destination_path)
            return response
        except Exception as e:
            self.logger.error(f"Failed to upload file to Supabase storage: {str(e)}", exc_info=True)
            return None

    def get_signed_url(self, bucket_name: str, file_path: str, expires_in_seconds: int = 3600) -> Optional[str]:
        """
        Generates a temporary signed URL for private bucket files.
        """
        if not self.supabase:
            return None
        try:
            res = self.supabase.storage.from_(bucket_name).create_signed_url(file_path, expires_in_seconds)
            return res.get("signedURL") if res else None
        except Exception as e:
            self.logger.error(f"Error generating signed URL: {str(e)}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """
        Deletes a file from the local filesystem.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Successfully deleted local file: {file_path}")
                return True
        except Exception as e:
            self.logger.error(f"Error deleting local file {file_path}: {str(e)}")
        return False
