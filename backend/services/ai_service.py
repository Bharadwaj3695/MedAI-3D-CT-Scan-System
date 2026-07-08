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

    def __init__(self, db: Optional[Any] = None, supabase_client: Optional[Any] = None):
        super().__init__(db, supabase_client)
        try:
            from chatbot.chatbot_agent import MedicalChatbotAgent
            self.chatbot_agent = MedicalChatbotAgent()
        except ImportError:
            self.chatbot_agent = None

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
        Generates a response for the medical AI assistant using MedicalChatbotAgent.
        """
        if self.chatbot_agent:
            return self.chatbot_agent.get_response(message, context)
        self.logger.error("MedicalChatbotAgent is not available.")
        return "Chatbot service is currently unavailable."


