# ADR-006: Selection of Grad-CAM for Model Explainability

* **Date**: June 30, 2026
* **Status**: Approved

## Context
In medical AI applications, black-box predictions (e.g., simply outputting "Malignant 95%") are insufficient. Radiologists must be able to verify *where* the model is looking to ensure it is not focusing on artifacts or background noise.

We considered:
1. **Saliency Maps**: Simple to compute, but highly noisy and difficult for clinicians to interpret.
2. **SHAP / LIME**: Model-agnostic, but computationally expensive for large 3D volumetric data.
3. **Grad-CAM**: Computes activation maps in a single backward pass, capturing coarse, high-level spatial features.

## Decision
We chose **Grad-CAM (Gradient-weighted Class Activation Mapping)** for explainable AI.

## Consequences
* **Positives**:
  - Fast computation: Adds negligible overhead to the inference pipeline.
  - Visually intuitive: Overlays a clear, color-coded heatmap showing the exact regions of high attention.
  - Helps detect model bias (e.g., if the model is classifying a scan based on the breathing tube rather than a lung nodule).
* **Negatives**:
  - Coarse resolution: The heatmap is limited by the spatial dimensions of the final convolutional layer (e.g., 8x8x8), resulting in a blurred overlay.
