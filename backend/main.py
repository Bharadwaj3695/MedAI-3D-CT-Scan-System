import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

from backend.config import settings
from backend.imaging_service import process_ct_scan
from backend.database import get_supabase

from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html

app = FastAPI(
    title="MedAI CT Scan API",
    description="AI-powered CT Scan Lung Nodule Detection",
    version="1.0",
    docs_url=None
)

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html(request: Request):
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + (app.openapi_url or "/openapi.json")
    oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if oauth2_redirect_url:
        oauth2_redirect_url = root_path + oauth2_redirect_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=oauth2_redirect_url,
        init_oauth=app.swagger_ui_init_oauth,
        swagger_ui_parameters=app.swagger_ui_parameters,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.12.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.12.0/swagger-ui.css",
    )

@app.get("/docs/oauth2-redirect", include_in_schema=False)
def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

from backend.routes.auth import router as auth_router
from backend.routes.scans import router as scans_router
from backend.routes.admin import router as admin_router
from backend.routes.reports import router as reports_router

app.include_router(auth_router, prefix="/api")
app.include_router(scans_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

@app.get("/api/debug/headers", tags=["debug"])
def debug_headers(request: Request):
    """
    TEMPORARY DIAGNOSTIC ENDPOINT (Do not use in production).
    
    Returns all incoming request headers, specifically highlighting:
    - Authorization
    - User-Agent
    - Host
    
    This endpoint is public, unprotected, and will be removed after testing.
    """
    headers_dict = dict(request.headers)
    return {
        "message": "TEMPORARY DIAGNOSTIC ENDPOINT - WILL BE REMOVED",
        "Authorization": headers_dict.get("authorization"),
        "User-Agent": headers_dict.get("user-agent"),
        "Host": headers_dict.get("host"),
        "all_headers": headers_dict
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory is managed via settings.UPLOAD_FOLDER


class AnalyzeRequest(BaseModel):
    scan_id: str
    file_url: str
    user_id: str

@app.post("/analyze/")
def analyze_scan_api(req: AnalyzeRequest, supabase = Depends(get_supabase)):
    try:
        # Download the file
        local_filename = req.file_url.split("/")[-1]
        # In case the URL query string is attached, split by '?' 
        local_filename = local_filename.split("?")[0]
        file_path = os.path.join(settings.UPLOAD_FOLDER, local_filename)

        response = requests.get(req.file_url)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        # Run CT pipeline
        result = process_ct_scan(file_path)

        # Prepare structured results according to the frontend's AnalysisResult interface
        structured_result = {
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "gradcam_base64": result.get("gradcam_base64"),
            "base_image_base64": result.get("base_image_base64"),
            "findings": [
                f"Detection logic identified: {result['prediction']}",
                "The image analysis has completed using the MedAI engine."
            ],
            "recommendations": [
                "Review findings with a certified radiologist",
                "Consider a follow-up scan based on the risk level"
            ],
            "risk_level": "high" if "malignant" in result["prediction"].lower() else "low"
        }

        # Save to analysis_results table
        if supabase is not None:
            # insert into analysis_results
            supabase.table("analysis_results").insert({
                "scan_id": req.scan_id,
                "user_id": req.user_id,
                "result_data": structured_result
            }).execute()

            # update scans status to completed
            supabase.table("scans").update({
                "status": "completed"
            }).eq("id", req.scan_id).execute()

        return {
            "status": "success",
            "data": structured_result
        }

    except Exception as e:
        if supabase is not None:
            # mark as failed
            supabase.table("scans").update({
                "status": "failed"
            }).eq("id", req.scan_id).execute()
        raise HTTPException(status_code=500, detail=str(e))


class AIChatRequest(BaseModel):
    message: str
    context: str = ""

@app.post("/api/ai-chat/")
@app.post("/ai-chat/")
def ai_chat(req: AIChatRequest):
    """
    Medical AI assistant chatbot endpoint.
    Routes requests to the centralized MedicalChatbotAgent.
    """
    try:
        from chatbot.chatbot_agent import MedicalChatbotAgent
        agent = MedicalChatbotAgent()
        reply = agent.get_response(req.message, req.context)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/predict/")
def predict_scan(file: UploadFile = File(...), supabase = Depends(get_supabase)):
    try:

        # Save uploaded file
        file_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run CT pipeline
        result = process_ct_scan(file_path)

        # Save to Supabase (if configured)
        if supabase is not None:
            supabase.table("scan_results").insert({
                "file_name": result["filename"],
                "prediction": result["prediction"],
                "confidence": result["confidence"]
            }).execute()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount the built frontend static directory
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Optional: mount public files if applicable (vite puts everything in dist)
    for f in os.listdir(frontend_dist):
        if os.path.isfile(os.path.join(frontend_dist, f)):
            @app.get(f"/{f}")
            def get_static_file(f=f):
                return FileResponse(os.path.join(frontend_dist, f))
    
    # Catch-all route to serve index.html for React Router
    @app.api_route("/{full_path:path}", methods=["GET"])
    def catch_all(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend build not found at " + index_path}
else:
    @app.api_route("/{full_path:path}", methods=["GET"])
    def catch_all_fallback(full_path: str):
        return {"message": "MedAI Backend Running (Frontend not built yet)"}