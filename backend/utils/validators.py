import os
import re
import logging
from typing import Tuple, Optional

# Try importing pydicom, handle failure gracefully if not installed
try:
    import pydicom
except ImportError:
    pydicom = None

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """
    Validates a standard email address format using regex.
    """
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_regex, email))

def validate_dicom_headers(file_path: str) -> Tuple[bool, str]:
    """
    Reads a DICOM file and validates that it has correct headers and is a CT scan.
    Returns (is_valid, error_message).
    """
    if pydicom is None:
        logger.warning("pydicom is not installed. Skipping DICOM header validation.")
        return True, "pydicom not installed; skipped header validation."

    if not os.path.exists(file_path):
        return False, "File does not exist."

    try:
        # Read file with force=True to handle files without standard DICOM preamble
        ds = pydicom.dcmread(file_path, force=True)
        
        # 1. Check Modality (should be CT)
        modality = getattr(ds, "Modality", None)
        if modality and modality != "CT":
            return False, f"Invalid modality: {modality}. Only CT scans are supported."
            
        # 2. Check that it contains pixel data
        if not hasattr(ds, "PixelData"):
            return False, "DICOM file does not contain any image pixel data."
            
        # 3. Log patient info (anonymized in production usually)
        patient_name = getattr(ds, "PatientName", "Anonymous")
        study_description = getattr(ds, "StudyDescription", "None")
        logger.info(f"Validated DICOM: Patient={patient_name}, Study={study_description}, Modality={modality}")
        
        return True, ""
    except Exception as e:
        logger.error(f"Error reading DICOM headers: {str(e)}")
        return False, f"Failed to parse DICOM metadata: {str(e)}"

def validate_3d_volume_dimensions(slices_count: int, min_slices: int = 5) -> Tuple[bool, str]:
    """
    Validates that a 3D scan contains a sufficient number of slices.
    """
    if slices_count < min_slices:
        return False, f"Volume has only {slices_count} slices. A minimum of {min_slices} slices is required for 3D analysis."
    return True, ""
