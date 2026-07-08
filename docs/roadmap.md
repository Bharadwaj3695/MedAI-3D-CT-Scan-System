# MedAI Roadmap

This document outlines the development milestones and future roadmap for the **MedAI-3D-CT-Scan-System**.

---

## Phase 1: Foundation & Refactoring (Completed)
- [x] Standardize UI components (`StatusBadge`, `StatsCard`, `EmptyState`, `LoadingSkeleton`).
- [x] Fix event-loop concurrency issues in the backend (move blocking ML inference to a threadpool).
- [x] Clean up page components and eliminate duplicate styling.
- [x] Introduce an interactive upload progress indicator with stage-by-stage simulations.

## Phase 2: Security & Standardization (Current)
- [ ] Implement a global React `ErrorBoundary` and centralized API error handler.
- [ ] Create a centralized frontend `api-client` to replace direct `fetch` calls.
- [ ] Standardize backend error responses and remove legacy duplicate routes in `main.py`.
- [ ] Implement JWT token expiration validation and auto-logout on the frontend.

## Phase 3: Advanced Imaging & Features (Near-Term)
- [ ] **Interactive 3D Slice Viewer**: Replace the static Grad-CAM slice visualization with an interactive slider allowing radiologists to scroll through the entire 3D volume (axial, sagittal, and coronal planes).
- [ ] **Multi-Class Classification**: Train and deploy a model capable of distinguishing between multiple lung diseases (e.g., Adenocarcinoma, Small Cell Carcinoma, Pneumonia, Tuberculosis) instead of a binary benign/malignant classification.
- [ ] **DICOM Metadata Parser**: Extract and display patient metadata (age, gender, scan date, slice thickness) directly from DICOM headers.

## Phase 4: Enterprise & Compliance (Long-Term)
- [ ] **HIPAA Compliance**: Implement audit logging, data anonymization on upload, and end-to-end encryption for patient-identifying data.
- [ ] **EHR Integration**: Support FHIR (Fast Healthcare Interoperability Resources) APIs to import scans directly from and export reports to Electronic Health Record (EHR) systems.
- [ ] **DICOM Web / PACS Integration**: Connect the system to hospital PACS (Picture Archiving and Communication System) using DICOMweb protocols.
