# AI Inference & Visualization Pipeline

The core value of the **MedAI-3D-CT-Scan-System** is its automated 3D Convolutional Neural Network (CNN) pipeline, which detects lung nodules and classifies scans into benign or malignant categories.

## Pipeline Workflow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Upload File    │ ──> │  Preprocessing   │ ──> │ 3D CNN Classifier│
│  (.nii / .dcm)   │     │  (Resample, HU)  │     │ (PyTorch Tensor) │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                           ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Grad-CAM Slice  │ <── │ Grad-CAM Mapping │ <── │   Prediction &   │
│ (Base64 Overlay) │     │ (Feature Act.)   │     │ Confidence Score │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## 1. Image Preprocessing
Raw CT scans come in varying voxel spacing and intensity scales. The preprocessing module (`backend/preprocess.py`) standardizes the volume:
1. **Format Loading**: Reads NIfTI files using `nibabel` or DICOM series using `pydicom`.
2. **Hounsfield Unit (HU) Windowing**: Lung tissue is typically visible between -1000 and -400 HU. The pipeline clips intensity values to `[-1000, 400]` and normalizes the range to `[0, 1]`.
3. **Resampling**: Standardizes voxel spacing to `(1.0, 1.0, 1.0) mm` using spline interpolation to ensure the model receives scale-invariant inputs.
4. **Cropping**: Isolates the lung bounding box to remove excess background noise (chest wall, air).

---

## 2. 3D CNN Classification Model
The classifier (`backend/model.py`) is a 3D ResNet-based architecture implemented in **PyTorch**:
- **Input**: A 3D tensor of shape `(1, 1, 128, 128, 128)` (Batch, Channels, Depth, Height, Width).
- **Architecture**:
  - 3D Convolutional layers with batch normalization and ReLU activations.
  - Residual blocks to prevent gradient degradation.
  - Global Average Pooling (GAP) before the fully connected classification head.
- **Output**: Softmax probabilities representing the risk of malignancy (Benign vs. Malignant/Adenocarcinoma).

---

## 3. Explainable AI: Grad-CAM
To assist radiologists in verifying the model's predictions, the system generates **Grad-CAM** (Gradient-weighted Class Activation Mapping) visualizations (`backend/gradcam.py`):
1. **Target Layer**: Captures feature maps from the final 3D convolutional layer (where spatial information is still preserved).
2. **Gradients**: Computes the gradients of the target class score with respect to the feature maps.
3. **Weighting**: Multiplies the feature maps by their corresponding gradients (importance weights) and applies a ReLU to capture only positive contributions to the class of interest.
4. **Heatmap Generation**:
   - Resizes the 3D heatmap back to the original CT scan size.
   - Extracts the 2D cross-sectional slice with the highest activation intensity.
   - Overlays the heatmap (red/yellow for high attention, blue/purple for low) onto the grayscale CT slice.
   - Encodes the overlay as a Base64 PNG for rendering in the React frontend.
