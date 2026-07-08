# MedAI Brain System Overview

The **MedAI-3D-CT-Scan-System** is an AI-powered medical imaging platform designed to automate the detection of lung nodules and analyze 3D CT scans. The "Brain" of the system represents the intersection of the React frontend, the FastAPI backend, and the Python-based 3D convolutional neural network (CNN) pipeline.

```
┌────────────────────────────────────────────────────────┐
│                        FOREGROUND                      │
│   React Frontend (Visualizes Grad-CAM & AI Reports)    │
└───────────────────────────┬────────────────────────────┘
                            │ (REST API + JSON)
┌───────────────────────────▼────────────────────────────┐
│                        MIDDLEWARE                      │
│   FastAPI Backend (Orchestration, Storage, & Security) │
└───────────────────────────┬────────────────────────────┘
                            │ (Local Path + NumPy)
┌───────────────────────────▼────────────────────────────┐
│                        BACKGROUND                      │
│   AI Pipeline (3D CT Preprocessing & PyTorch Inference)│
└────────────────────────────────────────────────────────┘
```

## Core Components

1. **User Interface (UI)**:
   - Provides drag-and-drop support for NIfTI (`.nii`, `.nii.gz`) and DICOM (`.dcm`) scan uploads.
   - Renders interactive canvas-based Grad-CAM heatmaps overlaying cross-sectional slices.
   - Facilitates real-time patient-doctor communication through an AI Medical Chatbot.

2. **Orchestration Layer (FastAPI)**:
   - Manages asynchronous uploads, file validation (caps at 150MB), and local scratch caching.
   - Conducts stateless JWT authentication and role-based access control (RBAC).
   - Triggers the AI pipeline synchronously inside threadpools to prevent blocking the event loop.

3. **Inference Pipeline**:
   - Parses 3D volumes, resamples voxel spacing, and normalizes Hounsfield Units (HU).
   - Feeds processed tensors to the 3D CNN classifier.
   - Computes prediction probability and extracts activation maps via Grad-CAM.
   - Generates structured clinical findings and recommendations.
