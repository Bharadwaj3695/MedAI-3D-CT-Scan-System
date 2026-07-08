# Security & Access Control

As a medical imaging platform, security and patient data privacy are top priorities for the **MedAI-3D-CT-Scan-System**. This document details the security measures implemented to ensure confidentiality, integrity, and availability.

---

## 1. Authentication

The system uses a **stateless, token-based authentication** flow:
- **Supabase Auth**: Serves as the identity provider, handling password verification, email confirmation, and third-party OAuth (Google).
- **JWT (JSON Web Tokens)**: Upon successful login, the backend issues a signed JWT access token.
  - The token payload includes the user ID (`sub`), email, and their assigned security role.
  - The token is signed using a secure algorithm (`HS256`) and verified on every protected request.
- **Token Storage**: The frontend stores the token in `localStorage` (`medai_token`) and attaches it as a `Bearer` token in the `Authorization` header of all API requests.

---

## 2. Authorization (Role-Based Access Control)

The system supports two primary security roles, defined in the `user_roles` database table:

| Role | Permissions |
| :--- | :--- |
| `user` | Can upload scans, view their own scan history, run AI predictions on their scans, and generate reports. |
| `admin` | Inherits all `user` permissions. In addition, can access the Admin Panel, view system-wide stats, and list all registered users and scans. |

### Enforcing Roles in FastAPI
The role check is implemented as a reusable dependency:
```python
def require_admin(current_user = Depends(get_current_user), supabase = Depends(get_supabase)):
    role_data = supabase.table("user_roles").select("role").eq("user_id", current_user.id).maybe_single().execute()
    if not role_data or role_data.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
```

---

## 3. Data Protection & Privacy

### Encryption
- **In-Transit**: All communications between the client, API gateway, and Supabase are encrypted using **TLS 1.3/HTTPS**.
- **At-Rest**: Supabase PostgreSQL database tables and S3 Storage buckets are encrypted at rest using industry-standard AES-256.

### File Sanitization
- File uploads are strictly validated in `backend/routes/scans.py` (`validate_scan_file`):
  - Limits file size to **150MB** to prevent Denial of Service (DoS) disk exhaustion.
  - Whitelists file extensions (`.nii`, `.nii.gz`, `.dcm`) to prevent execution of malicious binary scripts.
- Uploaded files are renamed to random UUIDs upon storage to prevent directory traversal attacks or exposing patient names in file paths.
