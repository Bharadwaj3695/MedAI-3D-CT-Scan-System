import os
from pathlib import Path
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    # ==========================================================================
    # Application Configuration
    # ==========================================================================
    # General application metadata and debug flags.
    APP_NAME: str = "MedAI 3D CT Scan System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ==========================================================================
    # Security Configuration
    # ==========================================================================
    # Cryptographic keys and expiration times for JWT tokens and encryption.
    SECRET_KEY: str = "super-secret-key-for-local-development-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # Default to 7 days (60 * 24 * 7)

    # ==========================================================================
    # Supabase Configuration
    # ==========================================================================
    # Connection parameters for the Supabase backend.
    SUPABASE_URL: str = ""
    
    # We support both SUPABASE_ANON_KEY and the legacy/existing SUPABASE_KEY 
    # for backwards compatibility with your current .env setup.
    SUPABASE_ANON_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "SUPABASE_KEY")
    )
    
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ==========================================================================
    # Storage Configuration
    # ==========================================================================
    # File paths for local temporary uploads and generated outputs.
    UPLOAD_FOLDER: str = str(BASE_DIR / "uploads")
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    OUTPUT_FOLDER: str = str(BASE_DIR / "outputs")

    # ==========================================================================
    # AI Model Configuration
    # ==========================================================================
    # Path to the AI model weight file or processing script.
    MODEL_PATH: str = str(BASE_DIR / "backend" / "model.py")

    # ==========================================================================
    # Settings Configuration
    # ==========================================================================
    # Pydantic Settings configuration to load variables from .env
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Export settings singleton
settings = Settings()

# Ensure configured folders exist
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(settings.OUTPUT_FOLDER, exist_ok=True)
