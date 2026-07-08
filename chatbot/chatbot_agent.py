import os
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("chatbot")

class MedicalChatbotAgent:
    """
    Agent responsible for handling patient and practitioner chatbot conversations.
    Supports OpenAI (or other configured LLM) and falls back to a rule-based matching engine.
    """

    def __init__(self):
        # Configure standard system prompt
        self.system_prompt = (
            "You are a helpful, professional medical AI assistant specializing in lung diseases and 3D CT scan interpretation.\n"
            "Always remind users to consult a certified radiologist for definitive clinical diagnoses.\n"
            "Keep your explanations clear, empathetic, and scientifically accurate."
        )

        # Standard rules for fallback response matching
        self.fallback_rules: List[Tuple[List[str], str]] = [
            (["malignant", "cancer", "tumor", "nodule"], 
             "A malignant finding indicates potentially cancerous tissue. This should be confirmed with a biopsy and reviewed by an oncologist. Early detection is critical — please schedule a follow-up with your physician immediately."),
            (["benign", "benign nodule", "no cancer", "cyst"],
             "A benign finding means the detected area or nodule is non-cancerous. While this is reassuring, periodic follow-up scans may still be recommended to monitor for any changes. Ensure you consult with your physician."),
            (["confidence", "accuracy", "how sure", "certain"],
             "The confidence score represents how certain the AI model is about its prediction (0–100%). A higher score means stronger visual evidence in the scan data. Always pair this with a clinical evaluation by a radiologist."),
            (["findings", "what does it mean", "explain results"],
             "The findings section summarizes key observations from the CT analysis. Each finding corresponds to specific patterns the AI detected in your scan. A radiologist can provide a full clinical interpretation."),
            (["recommendation", "next steps", "what should i do"],
             "Common next steps include: scheduling a follow-up scan in 3–6 months, consulting a pulmonologist, and discussing risk factors with your physician. Treatment options depend on the severity and nature of the findings."),
            (["lung nodule", "pulmonary nodule"],
             "A pulmonary nodule is a small, rounded abnormality in the lung. Most are benign, but some may require monitoring or further evaluation depending on size, shape, and growth rate."),
            (["dicom", "nifti", "file format", "ct scan format"],
             "MedAI supports DICOM (.dcm) and NIfTI (.nii, .nii.gz) — standard medical imaging formats — as well as regular images like PNG and JPEG for quick analysis."),
            (["grad-cam", "heatmap", "visualization"],
             "The Grad-CAM heatmap highlights the regions of the CT scan that most influenced the AI's decision. Red areas indicate high attention from the model — these are where the detected abnormality likely exists."),
            (["risk", "high risk", "low risk", "moderate"],
             "Risk level is derived from the AI prediction: high risk (likely malignant), moderate (monitoring recommended), or low (likely benign). This is a preliminary assessment and should be verified clinically."),
            (["hello", "hi", "hey", "help", "greet"],
             "Hello! I am your MedAI medical assistant. I can help you understand CT scan results, explain findings, or answer questions about lung conditions. How can I help you today?"),
        ]

    def get_response(self, message: str, context: Optional[str] = None) -> str:
        """
        Main interface to generate a response.
        Loads OpenAI if key is present, otherwise falls back to rule-based.
        """
        msg = message.lower()
        
        # 1. Attempt OpenAI call
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                # Handle newer openai client API (>1.0.0)
                client = openai.OpenAI(api_key=openai_key)
                
                full_system_prompt = self.system_prompt
                if context:
                    full_system_prompt += f"\nContext from latest scan: {context}"
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI completion failed: {e}", exc_info=True)

        # 2. Rule-based fallback
        for keywords, response_text in self.fallback_rules:
            if any(kw in msg for kw in keywords):
                return response_text

        # 3. Default general response
        return (
            "Thank you for your question. For specific medical advice, please consult a licensed radiologist or physician. "
            "I can help explain CT scan findings, medical terminology, or general information about lung conditions. "
            "Could you provide more details about what you'd like to know?"
        )
