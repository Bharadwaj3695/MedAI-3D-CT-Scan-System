import os
from backend.preprocess import preprocess_ct
from backend.model import load_model, predict

# Load model once when server starts
model = load_model()


import base64
from backend.gradcam import generate_gradcam

def process_ct_scan(file_path: str):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CT scan file not found: {file_path}")

    # Step 1: Preprocess CT scan
    processed_scan = preprocess_ct(file_path)

    # Step 2: Run prediction
    prediction, confidence = predict(model, processed_scan)

    # Step 3: Generate GradCAM heatmap and Base Image
    paths = generate_gradcam(model, processed_scan)
    
    encoded_gradcam = None
    encoded_base = None

    if os.path.exists(paths["gradcam_path"]):
        with open(paths["gradcam_path"], "rb") as image_file:
            encoded_gradcam = base64.b64encode(image_file.read()).decode("utf-8")
            
    if os.path.exists(paths["base_path"]):
        with open(paths["base_path"], "rb") as image_file:
            encoded_base = base64.b64encode(image_file.read()).decode("utf-8")

    # Step 4: Return structured result
    result = {
        "filename": os.path.basename(file_path),
        "prediction": prediction,
        "confidence": float(confidence),
        "gradcam_base64": encoded_gradcam,
        "base_image_base64": encoded_base
    }

    return result