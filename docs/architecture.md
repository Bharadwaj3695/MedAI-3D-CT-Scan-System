# System Architecture

This document describes the high-level architecture of the **MedAI-3D-CT-Scan-System**. The application utilizes a decoupled client-server architecture with a React-based Single Page Application (SPA) on the frontend and a FastAPI REST API on the backend, using Supabase for cloud database and object storage.

## High-Level Component Diagram

```mermaid
graph TB
    subgraph Client [Frontend Client]
        SPA[React SPA]
        RC[React Query Cache]
        AuthCtx[Auth Context]
    end

    subgraph API [API Layer]
        FastAPI[FastAPI Gateway]
        AuthRouter[Auth Router]
        ScanRouter[Scan Router]
        ReportRouter[Report Router]
        AdminRouter[Admin Router]
    end

    subgraph Service [Service Layer]
        AISvc[AI Inference Service]
        StorageSvc[Storage Service]
        ReportSvc[Report Service]
    end

    subgraph Cloud [Supabase Cloud]
        DB[(PostgreSQL Database)]
        Storage[[(S3 Object Storage)]]
        SAuth[Supabase Auth]
    end

    SPA -->|HTTPS + JWT| FastAPI
    FastAPI --> AuthRouter
    FastAPI --> ScanRouter
    FastAPI --> ReportRouter
    FastAPI --> AdminRouter

    ScanRouter --> AISvc
    ScanRouter --> StorageSvc
    ReportRouter --> ReportSvc

    StorageSvc -->|Upload/Delete| Storage
    ReportSvc -->|SQL Query| DB
    AuthRouter -->|Sign In/Up| SAuth
    
    AISvc -->|Local File IO| Disk[(Local Disk Cache)]
```

## Data Flow: Upload & Analyze

1. **Upload Request**: The user selects a 3D CT scan file (`.nii.gz`) and clicks **Upload & Analyze**. The React app sends a `multipart/form-data` request to `/api/scans/upload`.
2. **Validation & Caching**: The `ScanRouter` validates the file size and extension, then uses `StorageService` to write the stream to a local scratch directory (`backend/uploads/`).
3. **Cloud Backup**: `StorageService` uploads the file to the Supabase `scans` bucket. The public URL is returned.
4. **Pending Record**: The router inserts a scan record into the `scans` table with `status="pending"`.
5. **AI Inference**: The router calls `AIService.run_ct_inference(local_path)` synchronously (executed in FastAPI's external threadpool).
   - The file is preprocessed.
   - The 3D CNN predicts malignant vs. benign status.
   - Grad-CAM extracts 2D attention slices.
6. **Results Persisted**: The analysis results (findings, recommendations, and base64-encoded Grad-CAM images) are inserted into the `analysis_results` table. The scan status is updated to `completed`.
7. **Redirection**: The frontend, polling or awaiting the upload response, receives the completed status and redirects the user to `/results/:scan_id` to render the visualization.
