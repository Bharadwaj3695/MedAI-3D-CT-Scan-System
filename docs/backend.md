# Backend Architecture

The backend of the **MedAI-3D-CT-Scan-System** is built using **FastAPI** (Python 3.10+). It acts as the orchestration layer, connecting the web client with the database and the machine learning inference pipeline.

## Directory Structure
```
backend/
├── routes/             # FastAPI routers (endpoints)
│   ├── auth.py         # Login, signup, token generation
│   ├── scans.py        # File upload, delete, stats, predict
│   ├── reports.py      # PDF/HTML report generation
│   └── admin.py        # System stats and user list
├── services/           # Business logic layer
│   ├── auth.py         # Password reset, OAuth URLs
│   ├── ai_service.py   # Runs PyTorch 3D CNN & Grad-CAM
│   ├── imaging.py      # Core image processing utilities
│   ├── report_service.ts # Formats HTML templates
│   └── storage_service.py # Handles local and Supabase I/O
├── utils/              # Helper utilities (logger, etc.)
├── main.py             # FastAPI app initialization & middleware
├── database.py         # Supabase client & SQLAlchemy setup
└── config.py           # Pydantic BaseSettings config
```

## Key Architectural Patterns

### 1. Separation of Concerns (Service-Layer Pattern)
Route handlers under `routes/` are thin. They are responsible only for parsing HTTP requests, verifying dependencies (e.g., authentication, database connections), and returning HTTP responses. All business logic is encapsulated within reusable classes under `services/`.

### 2. Event Loop Concurrency & Threadpool Offloading
FastAPI runs on an asynchronous ASGI server (Uvicorn). Heavy operations like loading a 3D NIfTI file, running a deep learning model, or performing blocking database queries can block the event loop if not handled correctly.
- **Async Endpoints (`async def`)**: Used only when we perform non-blocking I/O (like awaiting `UploadFile.read()`).
- **Sync Endpoints (`def`)**: Used for CPU-bound tasks (e.g., `predict_scan`) or blocking DB queries. FastAPI automatically runs these endpoints in an external threadpool, ensuring the main event loop remains responsive.

### 3. Dependency Injection (DI)
FastAPI's `Depends` is used extensively for:
- Database clients (`get_supabase`).
- Authentication checks (`get_current_user`).
- Instantiating services (`get_ai_service`, `get_storage_service`).

This allows us to easily swap implementations (e.g., inject a mock Supabase client during testing).
