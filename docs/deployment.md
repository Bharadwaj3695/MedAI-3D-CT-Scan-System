# Deployment Guide

This document describes how to deploy the **MedAI-3D-CT-Scan-System** to staging or production environments.

---

## 1. Environment Variables

The application requires configuration via environment variables. These should be set in a `.env` file in the root directory (for local development) or injected into the container/host environment.

### Backend Configurations
```ini
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
JWT_SECRET=your_jwt_signing_secret_key
UPLOAD_DIR=uploads/
OUTPUT_FOLDER=outputs/
```

### Frontend Configurations
```ini
VITE_SUPABASE_URL=https://your-supabase-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

---

## 2. Docker Deployment

We recommend containerizing the backend for consistency across cloud providers.

### `Dockerfile` (Backend)
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV / medical image processing
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

To build and run:
```bash
docker build -t medai-backend .
docker run -p 8000:8000 --env-file .env medai-backend
```

---

## 3. Hosting Recommendations

### Frontend (Static SPA)
The React frontend can be compiled into static assets and hosted on global CDNs:
- **Vercel** or **Netlify**:
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - Configure redirects to support client-side routing (e.g., a `vercel.json` or `_redirects` file mapping all routes to `index.html`).

### Backend (FastAPI + PyTorch)
Since the backend runs PyTorch model inference, it requires a host with sufficient CPU/RAM (minimum 2GB RAM recommended):
- **Render** or **Railway**: Easy deployment from GitHub, supports Dockerfiles, and manages SSL certificates automatically.
- **AWS ECS (Fargate)**: For production deployments needing high availability, auto-scaling, and VPC isolation.
- **AWS EC2 / GCP Compute Engine**: For workloads requiring dedicated GPU acceleration (CUDA).
