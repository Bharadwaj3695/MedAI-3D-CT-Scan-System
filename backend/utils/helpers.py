import os
import uuid
from typing import Set, Tuple
from pathlib import Path

# Set of allowed extensions for medical imaging and general uploads
ALLOWED_EXTENSIONS: Set[str] = {
    # Medical scans
    ".dcm", ".dicom",  # DICOM
    ".nii", ".nii.gz",  # NIfTI
    ".mhd", ".mha",     # MetaImage
    ".raw",             # Raw binary
    # Archives (multi-slice DICOM folders)
    ".zip", ".tar", ".gz",
    # Images (preprocessed / results / reports)
    ".png", ".jpg", ".jpeg", ".webp"
}

MAX_FILE_SIZE_MB = 250  # 250MB limit for 3D scans

def allowed_file(filename: str) -> bool:
    """
    Checks if a file extension is in the list of allowed extensions.
    Supports double extensions like .nii.gz
    """
    filename_lower = filename.lower()
    
    # Check for double extensions first (e.g. .nii.gz)
    for ext in ALLOWED_EXTENSIONS:
        if ext.count('.') > 1 and filename_lower.endswith(ext):
            return True
            
    # Check for single extensions
    _, ext = os.path.splitext(filename_lower)
    return ext in ALLOWED_EXTENSIONS

def get_safe_filename(filename: str) -> str:
    """
    Generates a unique, safe filename using UUID to prevent naming collisions.
    Preserves the original extension.
    """
    # Handle double extensions like .nii.gz
    suffix = ""
    filename_lower = filename.lower()
    for ext in ALLOWED_EXTENSIONS:
        if ext.count('.') > 1 and filename_lower.endswith(ext):
            suffix = ext
            break
            
    if not suffix:
        suffix = Path(filename).suffix

    unique_id = uuid.uuid4().hex
    return f"{unique_id}{suffix}"

def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Validates that the file size does not exceed the maximum permitted size.
    file_size: size in bytes
    """
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File size exceeds the limit of {MAX_FILE_SIZE_MB}MB."
    return True, ""

def format_size(size_in_bytes: int) -> str:
    """
    Formats bytes into a human-readable string (KB, MB, GB).
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"
