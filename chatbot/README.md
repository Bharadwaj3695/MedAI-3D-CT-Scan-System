# Chatbot Service

This directory contains the conversational AI agent logic for the MedAI-3D-CT-Scan-System.

## Features
- **Intelligent Conversations**: Answers patient and doctor queries regarding CT scans, nodules, and general lung health.
- **Multi-Engine Support**: Seamlessly connects to OpenAI or Gemini when keys are provided, falling back to a structured rule-based response system for local-only setups.
- **Medical Disclaimer**: Automatically appends appropriate disclaimers, reminding users that the system is a diagnostic aid and not a replacement for professional clinical judgment.

## Usage
The FastAPI backend imports `MedicalChatbotAgent` from `chatbot.chatbot_agent` to handle the `/api/ai-chat/` endpoint.
