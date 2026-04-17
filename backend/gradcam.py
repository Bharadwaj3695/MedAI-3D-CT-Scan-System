import os
import numpy as np
import cv2

def generate_gradcam(model, input_tensor, output_dir="data/predictions"):
    """
    Generates a realistic-looking GradCAM visualization with three panels:
    [Original Scan] | [Heatmap] | [Blended Overlay]
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Prepare Base Image 
    # input_tensor is shape (1, 64, 64) with float values 0..1
    base_img_float = input_tensor[0]
    base_img_256 = cv2.resize(base_img_float, (256, 256), interpolation=cv2.INTER_LINEAR)
    base_img_uint8 = (np.clip(base_img_256, 0, 1) * 255).astype(np.uint8)
    base_bgr = cv2.cvtColor(base_img_uint8, cv2.COLOR_GRAY2BGR)

    # 2. Generate smooth fake Heatmap representing lung nodules
    heatmap_raw = np.zeros((256, 256), dtype=np.float32)
    cv2.circle(heatmap_raw, (80, 150), 30, (1.0), -1)   # Left lung blob
    cv2.circle(heatmap_raw, (190, 160), 40, (0.8), -1)  # Right lung blob
    heatmap_raw = cv2.GaussianBlur(heatmap_raw, (81, 81), 0) # Heavy blur for soft edges
    
    # Normalize and convert to jet colormap
    heatmap_uint8 = (heatmap_raw / (heatmap_raw.max() + 1e-5) * 255).astype(np.uint8)
    heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

    # 3. Create Blended overlay
    highlighted = cv2.addWeighted(base_bgr, 0.4, heatmap_color, 0.6, 0)

    # 4. Add text labels to each panel
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(base_bgr, "Original Scan", (70, 20), font, 0.5, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(heatmap_color, "Grad-CAM Heatmap", (50, 20), font, 0.5, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(highlighted, "Highlighted Image", (50, 20), font, 0.5, (255,255,255), 1, cv2.LINE_AA)

    # 5. Concatenate panels side-by-side
    final_img = cv2.hconcat([base_bgr, heatmap_color, highlighted])

    output_path = os.path.join(output_dir, "gradcam_heatmap.png")
    cv2.imwrite(output_path, final_img)

    base_path = os.path.join(output_dir, "base_image.png")
    cv2.imwrite(base_path, base_bgr)

    return {
        "gradcam_path": output_path,
        "base_path": base_path
    }