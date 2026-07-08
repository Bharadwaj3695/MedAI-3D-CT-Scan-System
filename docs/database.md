# Database Schema & Integration

The **MedAI-3D-CT-Scan-System** uses **Supabase** (PostgreSQL) as its primary database. The schema is designed to manage users, scan metadata, AI analysis results, generated reports, and security roles.

## Entity Relationship Diagram

```
  ┌──────────────┐          ┌─────────────┐          ┌──────────────────┐
  │   profiles   │ 1      1 │  user_roles │          │      scans       │
  ├──────────────┤──────────├─────────────┤          ├──────────────────┤
  │ id (PK)      │          │ user_id (FK)│          │ id (PK)          │
  │ email        │          │ role        │          │ user_id (FK)     │
  │ full_name    │          └─────────────┘          │ file_name        │
  │ created_at   │                 │ 1               │ file_path        │
  └──────────────┘                 │                 │ file_url         │
         │ 1                       │                 │ status           │
         │                         │                 │ created_at       │
         │                         │                 └──────────────────┘
         │                         │                           │ 1
         │                         │                           │
         │                         │                           │ 1
         │                         │                 ┌──────────────────┐
         │                         │                 │ analysis_results │
         │                         │                 ├──────────────────┤
         │                         │                 │ id (PK)          │
         │                         └─────────────────│ scan_id (FK)     │
         │                                           │ user_id (FK)     │
         │                                           │ result_data      │
         │                                           └──────────────────┘
         │                                                     │
         │ 1                                                   │ 1
         └─────────────────────────────────────────────────────┘
```

## Table Specifications

### 1. `profiles`
Stores user profile information. Linked directly to Supabase Auth's internal `auth.users` table.
- `id` (uuid, PK, references `auth.users.id` ON DELETE CASCADE)
- `email` (varchar, unique)
- `full_name` (varchar)
- `avatar_url` (text, optional)
- `created_at` (timestamp with time zone)
- `updated_at` (timestamp with time zone)

### 2. `user_roles`
Stores role assignment for Role-Based Access Control (RBAC).
- `user_id` (uuid, PK, references `auth.users.id` ON DELETE CASCADE)
- `role` (varchar, default 'user') — supports `'user'` and `'admin'`.

### 3. `scans`
Stores metadata of uploaded 3D scans.
- `id` (uuid, PK, default `gen_random_uuid()`)
- `user_id` (uuid, FK, references `auth.users.id` ON DELETE CASCADE)
- `file_name` (varchar)
- `file_path` (varchar) — path in the Supabase Storage bucket
- `file_url` (varchar) — public access URL
- `scan_type` (varchar, default 'CT')
- `notes` (text, optional)
- `status` (varchar, default 'pending') — `'pending'`, `'processing'`, `'completed'`, `'failed'`
- `created_at` (timestamp with time zone, default `now()`)

### 4. `analysis_results`
Stores the structured outputs of the AI inference pipeline.
- `id` (uuid, PK, default `gen_random_uuid()`)
- `scan_id` (uuid, FK, references `scans.id` ON DELETE CASCADE)
- `user_id` (uuid, FK, references `auth.users.id` ON DELETE CASCADE)
- `result_data` (jsonb) — stores predictions, confidence score, findings, recommendations, and base64-encoded Grad-CAM images.
- `created_at` (timestamp with time zone, default `now()`)

### 5. `reports`
Stores metadata of generated clinical reports.
- `id` (uuid, PK, default `gen_random_uuid()`)
- `scan_id` (uuid, FK, references `scans.id` ON DELETE CASCADE)
- `user_id` (uuid, FK, references `auth.users.id` ON DELETE CASCADE)
- `title` (varchar)
- `summary` (text)
- `created_at` (timestamp with time zone, default `now()`)

---

## Row-Level Security (RLS) Policies
To ensure HIPAA compliance and data privacy, RLS is enabled on all tables:
- **`scans`**:
  - `SELECT`: `auth.uid() = user_id` (Users can only view their own scans). Admins bypass this check.
  - `INSERT`: `auth.uid() = user_id`.
  - `DELETE`: `auth.uid() = user_id`.
- **`analysis_results`** & **`reports`**:
  - `SELECT`: `auth.uid() = user_id`.
  - `INSERT`: `auth.uid() = user_id`.
