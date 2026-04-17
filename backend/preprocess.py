import numpy as np
import os

def preprocess_ct(file_path: str):
    """
    Load a CT scan image file (PNG/JPEG/DICOM/NIfTI) and preprocess it
    into a normalized 64x64 numpy array for model inference.
    Supports: .nii, .nii.gz (NIfTI), .dcm (DICOM), .png, .jpg, .jpeg, .bmp
    """
    # Handle double extension like .nii.gz
    fname = os.path.basename(file_path).lower()
    if fname.endswith('.nii.gz'):
        ext = '.nii.gz'
    else:
        ext = os.path.splitext(file_path)[-1].lower()

    try:
        if ext in ['.nii', '.nii.gz']:
            # NIfTI file (your KiTS dataset format)
            import nibabel as nib
            img = nib.load(file_path)
            data = img.get_fdata()
            # Take middle axial slice (axis 2 = axial for standard NIfTI)
            mid = data.shape[2] // 2
            pixel_array = data[:, :, mid].astype(np.float32)
            # CT Hounsfield Unit windowing: lung window [-1000, 400]
            pixel_array = np.clip(pixel_array, -1000, 400)

        elif ext == '.dcm':
            # DICOM file
            import pydicom
            ds = pydicom.dcmread(file_path)
            pixel_array = ds.pixel_array.astype(np.float32)
            # Apply DICOM rescale if available
            slope = float(getattr(ds, 'RescaleSlope', 1))
            intercept = float(getattr(ds, 'RescaleIntercept', 0))
            pixel_array = pixel_array * slope + intercept
            # Take middle slice if 3D
            if len(pixel_array.shape) == 3:
                pixel_array = pixel_array[pixel_array.shape[0] // 2]
            # CT windowing
            pixel_array = np.clip(pixel_array, -1000, 400)

        else:
            # Standard image (PNG, JPEG, BMP, etc.)
            from PIL import Image
            img = Image.open(file_path).convert('L')  # Grayscale
            pixel_array = np.array(img, dtype=np.float32)

        # Resize to 64x64 using PIL
        from PIL import Image
        # Normalize range before converting to PIL image
        p_min, p_max = pixel_array.min(), pixel_array.max()
        if p_max > p_min:
            norm_for_resize = ((pixel_array - p_min) / (p_max - p_min) * 255).astype(np.uint8)
        else:
            norm_for_resize = np.zeros_like(pixel_array, dtype=np.uint8)

        pil_img = Image.fromarray(norm_for_resize)
        pil_img = pil_img.resize((64, 64), Image.LANCZOS)
        pixel_array = np.array(pil_img, dtype=np.float32) / 255.0  # Normalize to [0, 1]

        # Add channel dim → shape (1, 64, 64)
        return pixel_array[np.newaxis, :]

    except Exception as e:
        print(f"WARNING: Could not preprocess real file '{file_path}' ({e}). Falling back to random data.")
        return np.random.rand(1, 64, 64).astype(np.float32)
