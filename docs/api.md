# API Reference

The **MedAI-3D-CT-Scan-System** backend provides a RESTful JSON API. All protected endpoints require a stateless JWT token passed via the `Authorization` header.

## Authentication Headers
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

---

## 1. Authentication Endpoints

### `POST /api/auth/signup`
Registers a new user account.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword123"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "user-uuid",
    "email": "user@example.com",
    "is_active": true,
    "profile": {
      "id": "user-uuid",
      "email": "user@example.com",
      "full_name": "User",
      "avatar_url": null,
      "created_at": "2026-06-30T16:00:00Z",
      "updated_at": null
    }
  }
  ```

### `POST /api/auth/login`
Authenticates a user and issues a JWT token.
- **Request Body** (`application/x-www-form-urlencoded`):
  - `username`: `user@example.com`
  - `password`: `strongpassword123`
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGci...",
    "token_type": "bearer"
  }
  ```

---

## 2. Scan Endpoints

### `POST /api/scans/upload` (Protected)
Uploads and schedules a 3D CT scan.
- **Request Body** (`multipart/form-data`):
  - `file`: `<Binary File>` (NIfTI or DICOM)
  - `scan_type`: `CT`
  - `notes`: `Optional clinical notes`
- **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "scan_id": "scan-uuid",
    "file_name": "patient_scan.nii.gz",
    "file_url": "https://supabase..."
  }
  ```

### `POST /api/scans/predict` (Protected)
Triggers or re-triggers AI inference on an uploaded scan.
- **Request Body**:
  ```json
  {
    "scan_id": "scan-uuid"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "scan_id": "scan-uuid",
    "status": "completed",
    "prediction_class": "Adenocarcinoma",
    "probability": 0.942,
    "heatmap_url": "data:image/png;base64,...",
    "created_at": "2026-06-30T16:00:00Z"
  }
  ```

### `GET /api/scans/history` (Protected)
Fetches the paginated scan history of the logged-in user.
- **Query Parameters**:
  - `limit`: `10` (default)
  - `offset`: `0` (default)
- **Response (200 OK)**:
  ```json
  [
    {
      "scan_id": "scan-uuid",
      "patient_id": "user-uuid",
      "status": "completed",
      "created_at": "2026-06-30T16:00:00Z",
      "prediction": {
        "scan_id": "scan-uuid",
        "status": "completed",
        "prediction_class": "Adenocarcinoma",
        "probability": 0.942,
        "heatmap_url": "data:image/png;base64,...",
        "created_at": "2026-06-30T16:00:00Z"
      }
    }
  ]
  ```

---

## 3. Reports Endpoints

### `POST /api/reports/generate/{scan_id}` (Protected)
Generates an HTML/PDF medical report for a completed scan.
- **Response (201 Created)**:
  ```json
  {
    "id": "report-uuid",
    "scan_id": "scan-uuid",
    "patient_id": "user-uuid",
    "report_text": "AI Classification: Adenocarcinoma. Confidence: 94.20%.",
    "generated_by": "MedAI-3D-System",
    "created_at": "2026-06-30T16:00:00Z"
  }
  ```

### `GET /api/reports/download/{report_id}` (Public)
Downloads the raw HTML file of the generated report.
- **Response (200 OK)**: `text/html` document stream.
