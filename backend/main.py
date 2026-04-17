import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

from backend.imaging_service import process_ct_scan
from backend.supabase_client import supabase

app = FastAPI(
    title="MedAI CT Scan API",
    description="AI-powered CT Scan Lung Nodule Detection",
    version="1.0"
)

from backend.routes.auth import router as auth_router
from backend.routes.scans import router as scans_router

app.include_router(auth_router, prefix="/api")
app.include_router(scans_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class AnalyzeRequest(BaseModel):
    scan_id: str
    file_url: str
    user_id: str

@app.post("/analyze/")
def analyze_scan_api(req: AnalyzeRequest):
    try:
        # Download the file
        local_filename = req.file_url.split("/")[-1]
        # In case the URL query string is attached, split by '?' 
        local_filename = local_filename.split("?")[0]
        file_path = os.path.join(UPLOAD_DIR, local_filename)

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

@app.post("/ai-chat/")
def ai_chat(req: AIChatRequest):
    """
    Rule-based medical AI assistant endpoint.
    Provides medically-relevant responses based on keywords in the user's message.
    Replace the rule-based logic with an LLM API call (OpenAI, Gemini, etc.) by
    setting OPENAI_API_KEY or GOOGLE_API_KEY in your .env file.
    """
    msg = req.message.lower()
    context = req.context

    # --- Optional: LLM via OpenAI ---
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            system_prompt = (
                "You are a helpful medical AI assistant specializing in lung diseases and CT scan interpretation. "
                "Always remind users to consult a certified radiologist for definitive diagnoses. "
                f"Context from latest scan: {context}" if context else
                "You are a helpful medical AI assistant specializing in lung diseases and CT scan interpretation."
            )
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": req.message}
                ],
                max_tokens=300
            )
            reply = response.choices[0].message.content
            return {"reply": reply}
        except Exception as e:
            print(f"OpenAI error: {e}")

    # --- Rule-based fallback ---
    rules = [
        (["malignant", "cancer", "tumor", "nodule"], 
         "A malignant finding indicates potentially cancerous tissue. This should be confirmed with a biopsy and reviewed by an oncologist. Early detection is critical — please schedule a follow-up with your physician immediately."),
        (["benign", "benign nodule", "no cancer"],
         "A benign finding means the detected area is non-cancerous. However, periodic follow-up scans may still be recommended to monitor for any changes over time."),
        (["confidence", "accuracy", "how sure", "certain"],
         "The confidence score represents how certain the AI model is about its prediction (0–100%). A higher score means stronger evidence in the scan data. Always pair this with a clinical evaluation."),
        (["findings", "what does it mean", "explain results"],
         "The findings section summarizes key observations from the CT analysis. Each finding corresponds to specific patterns the AI detected in your scan. A radiologist can provide a full interpretation."),
        (["recommendation", "next steps", "what should i do"],
         "Common next steps include: scheduling a follow-up scan in 3–6 months, consulting a pulmonologist, and discussing risk factors with your physician. Treatment options depend on the severity and nature of the finding."),
        (["lung nodule", "pulmonary nodule"],
         "A pulmonary nodule is a small, rounded abnormality in the lung. Most are benign, but some may require monitoring or further evaluation depending on size, shape, and growth rate."),
        (["dicom", "nifti", "file format", "ct scan format"],
         "MedAI supports DICOM (.dcm) and NIfTI (.nii, .nii.gz) — standard medical imaging formats — as well as regular images like PNG and JPEG for quick analysis."),
        (["grad-cam", "heatmap", "visualization"],
         "The Grad-CAM heatmap highlights the regions of the CT scan that most influenced the AI decision. Red areas indicate high attention from the model — these are where the detected abnormality likely exists."),
        (["risk", "high risk", "low risk", "moderate"],
         "Risk level is derived from the AI prediction: high risk (likely malignant), moderate (uncertain, monitoring recommended), or low (likely benign). This is a preliminary assessment and should be verified clinically."),
        (["hello", "hi", "hey", "help"],
         "Hello! I'm the MedAI medical assistant. I can help you understand CT scan results, explain findings, or answer questions about lung conditions. What would you like to know?"),
    ]

    for keywords, response_text in rules:
        if any(kw in msg for kw in keywords):
            return {"reply": response_text}

    # General fallback
    return {
        "reply": (
            "Thank you for your question. For specific medical advice, please consult a licensed radiologist or physician. "
            "I can help explain CT scan findings, medical terminology, or general information about lung conditions. "
            "Could you provide more details about what you'd like to know?"
        )
    }



@app.post("/predict/")
async def predict_scan(file: UploadFile = File(...)):
    try:

        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)

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