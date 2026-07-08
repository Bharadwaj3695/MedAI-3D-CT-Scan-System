# ADR-005: Selection of PyTorch for AI Pipeline

* **Date**: June 30, 2026
* **Status**: Approved

## Context
3D CT scans represent spatial volumetric data. We need a deep learning framework to build, train, and run inference on a 3D Convolutional Neural Network (3D CNN).

We considered:
1. **TensorFlow / Keras**: Good production serving, but 3D convolutions and custom gradient hooks (for Grad-CAM) can be verbose.
2. **PyTorch**: Excellent Python integration, dynamic computation graphs, and strong community support for medical imaging (e.g., MONAI).

## Decision
We chose **PyTorch** as our deep learning framework.

## Consequences
* **Positives**:
  - Easier implementation of custom 3D CNN architectures.
  - Straightforward access to layer gradients, making Grad-CAM implementation highly maintainable.
  - Native integration with Python scientific libraries (`numpy`, `scipy`, `nibabel`).
* **Negatives**:
  - PyTorch models have a large memory footprint, requiring at least 2GB of RAM on the host server during inference.
