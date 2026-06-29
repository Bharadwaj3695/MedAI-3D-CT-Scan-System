import os
from typing import Dict, Any, Optional
from backend.services.base import BaseService
from backend.config import settings

# Import existing model and visualization functions
try:
    from backend.imaging_service import process_ct_scan
except ImportError:
    process_ct_scan = None

class AIService(BaseService):
    """
    Service to handle AI model inference, Grad-CAM generation,
    and conversational AI chatbot interactions.
    """

    def run_ct_inference(self, file_path: str) -> Dict[str, Any]:
        """
        Runs the 3D CT Scan analysis pipeline on the given file path.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CT scan file not found at: {file_path}")

        if process_ct_scan is None:
            self.logger.error("process_ct_scan is not available.")
            raise NotImplementedError("CT scan processing pipeline is not configured.")

        self.logger.info(f"Running AI inference on file: {file_path}")
        return process_ct_scan(file_path)

    def get_ai_chat_response(self, message: str, context: str = "") -> str:
        """
        Generates a response for the medical AI assistant.
        Uses OpenAI/Gemini if configured in environment, otherwise falls back to rule-based matching.
        """
        msg = message.lower()
        
        # 1. Attempt LLM API call if key is present
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
                        {"role": "user", "content": message}
                    ],
                    max_tokens=300
                )
                return response.choices[0].message.content
            except Exception as e:
                self.logger.error(f"OpenAI Chat completion failed: {str(e)}")

        # 2. Rule-based fallback
        rules = [
            (["malignant", "cancer", "tumor", "nodule"], 
             "A malignant finding indicates potentially cancerous tissue. This should be confirmed with a biopsy and reviewed by an oncologist. Early detection is critical — please schedule a follow-up with your physician immediately."),
            (["benign", "cyst"], 
             "A benign finding means the tissue or nodule is non-cancerous. While this is reassuring, some benign nodules require monitoring. Ensure you follow up with your doctor as scheduled."),
            (["dicom", "nifti", "upload", "format"], 
             "You can upload 3D CT scans in DICOM (.dcm) or NIfTI (.nii, .nii.gz) format. Our system will process the slices and run nodule detection."),
            (["gradcam", "grad-cam", "heatmap", "visualization"], 
             "Grad-CAM provides a visual heatmap highlighting the regions in the CT scan that the AI model focused on when making its prediction. Red areas indicate high importance."),
            (["hi", "hello", "help", "greet"], 
             "Hello! I am your MedAI assistant. I can help explain CT scan findings, explain what benign/malignant means, or guide you on how to upload scans. How can I help you today?")
        ]

        for keywords, response_text in rules:
            if any(kw in msg for kw in keywords):
                return response_text

        return (
            "I'm here to help with questions about your 3D CT scans, nodules, or how the AI model works. "
            "For specific medical concerns, please consult a healthcare professional."
        )
