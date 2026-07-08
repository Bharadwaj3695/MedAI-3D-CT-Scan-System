# Model Weights Store

This directory is designated for storing machine learning model weight files used by the 3D CT scan classification and segmentation pipeline.

## Storage Guidelines
- **File formats**: Pre-trained weights should be stored as PyTorch checkpoint files (`.pth` or `.pt`).
- **Git Tracking**: Due to file size limitations, binary model weight files (`*.pth`, `*.pt`) are ignored by Git in `.gitignore`. They must be downloaded or copied into this directory during deployment or setup.

## Current Target Models
- `lung_nodule_model.pth`: 3D CNN model weights for binary nodule malignancy classification.
