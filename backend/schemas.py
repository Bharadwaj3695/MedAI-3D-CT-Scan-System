"""
Pydantic Schemas Module.

This module defines the data transfer objects (DTOs) and validation schemas
for the MedAI 3D CT Scan System. The schemas are organized into logical sections:
1. Authentication Schemas
2. User Schemas
3. CT Scan Schemas
4. Report Schemas
5. AI and Model Inference Schemas
6. Backward Compatibility Schemas (matching existing inline route models)

All schemas use Pydantic v2 syntax and incorporate validation where appropriate.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ==============================================================================
# 1. Authentication Schemas
# ==============================================================================

class UserCreate(BaseModel):
    """
    Schema for user registration requests.
    """
    email: EmailStr = Field(..., description="Valid email address for the new user")
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=72, 
        description="Password for the new account (must be between 8 and 72 characters)"
    )


class UserLogin(BaseModel):
    """
    Schema for user login requests.
    """
    email: EmailStr = Field(..., description="Registered email address of the user")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """
    Schema for returning access tokens to the client.
    """
    access_token: str = Field(..., description="The cryptographically signed JWT access token")
    token_type: str = Field("bearer", description="The type of token (typically 'bearer')")


class TokenData(BaseModel):
    """
    Schema representing the payload/claims decoded from a JWT token.
    """
    user_id: Optional[str] = Field(None, description="The subject of the token (unique user ID)")
    email: Optional[EmailStr] = Field(None, description="Email address associated with the token")
    role: Optional[str] = Field(None, description="User authorization role (e.g., admin, user)")


# ==============================================================================
# 2. User Schemas
# ==============================================================================

class UserProfile(BaseModel):
    """
    Schema representing the detailed profile of a user.
    """
    id: str = Field(..., description="Unique profile identifier corresponding to the user ID")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="Full name of the user")
    avatar_url: Optional[str] = Field(None, description="URL of the user's avatar image")
    created_at: datetime = Field(..., description="Timestamp when the profile was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the profile was last updated")

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """
    Schema for returning user account details in API responses.
    """
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    is_active: bool = Field(True, description="Indicates if the user account is active")
    profile: Optional[UserProfile] = Field(None, description="Associated profile details")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 3. CT Scan Schemas
# ==============================================================================

class ScanUploadRequest(BaseModel):
    """
    Schema for uploading or initiating a new CT scan.
    """
    patient_id: str = Field(..., description="Unique identifier for the patient")
    scan_type: str = Field("CT", description="The imaging modality (e.g., CT, MRI)")
    notes: Optional[str] = Field(None, description="Optional clinical notes or observations")


class ScanPredictionResponse(BaseModel):
    """
    Schema for returning AI prediction results of a specific CT scan.
    """
    scan_id: str = Field(..., description="Unique identifier of the scan")
    status: str = Field(
        ..., 
        description="Current processing status of the scan (pending, processing, completed, failed)"
    )
    prediction_class: Optional[str] = Field(None, description="AI predicted classification (e.g., tumor, normal)")
    probability: Optional[float] = Field(None, description="AI prediction confidence probability (0.0 to 1.0)")
    heatmap_url: Optional[str] = Field(None, description="URL to the generated Grad-CAM heatmap visualization")
    created_at: datetime = Field(..., description="Timestamp when the scan was created")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("probability")
    @classmethod
    def validate_probability(cls, v: Optional[float]) -> Optional[float]:
        """
        Validates that the probability is within the valid [0.0, 1.0] range.
        """
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Probability must be between 0.0 and 1.0 inclusive.")
        return v


class ScanHistoryResponse(BaseModel):
    """
    Schema for returning a scan's historical record and associated prediction.
    """
    scan_id: str = Field(..., description="Unique identifier of the scan")
    patient_id: str = Field(..., description="Unique identifier of the patient")
    status: str = Field(..., description="Processing status of the scan")
    created_at: datetime = Field(..., description="Timestamp when the scan was created")
    prediction: Optional[ScanPredictionResponse] = Field(None, description="The AI prediction details if available")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 4. Report Schemas
# ==============================================================================

class ReportResponse(BaseModel):
    """
    Schema for returning a generated medical report.
    """
    id: str = Field(..., description="Unique identifier of the report")
    scan_id: str = Field(..., description="Identifier of the associated CT scan")
    patient_id: str = Field(..., description="Identifier of the patient")
    report_text: str = Field(..., description="The generated medical findings and report text")
    generated_by: str = Field(..., description="Identifier of the system or clinician who generated the report")
    created_at: datetime = Field(..., description="Timestamp when the report was generated")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 5. AI and Model Inference Schemas
# ==============================================================================

class PredictionResult(BaseModel):
    """
    Schema representing a raw AI model prediction result.
    """
    prediction_class: str = Field(..., description="Predicted class or classification label")
    probability: float = Field(..., description="Prediction confidence probability (0.0 to 1.0)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata from the AI inference engine")

    @field_validator("probability")
    @classmethod
    def validate_probability(cls, v: float) -> float:
        """
        Validates that the probability is within the valid [0.0, 1.0] range.
        """
        if not (0.0 <= v <= 1.0):
            raise ValueError("Probability must be between 0.0 and 1.0 inclusive.")
        return v


class HeatmapResponse(BaseModel):
    """
    Schema representing heatmap visualization metadata.
    """
    heatmap_url: str = Field(..., description="URL to the generated Grad-CAM heatmap visualization image")
    overlay_opacity: float = Field(
        0.5, 
        description="Suggested opacity for overlaying the heatmap on the original image (0.0 to 1.0)"
    )

    @field_validator("overlay_opacity")
    @classmethod
    def validate_opacity(cls, v: float) -> float:
        """
        Validates that the opacity is within the valid [0.0, 1.0] range.
        """
        if not (0.0 <= v <= 1.0):
            raise ValueError("Overlay opacity must be between 0.0 and 1.0 inclusive.")
        return v


# ==============================================================================
# 6. Backward Compatibility Schemas (matching existing inline route models)
# ==============================================================================

class AnalyzeRequest(BaseModel):
    """
    Schema matching the existing AnalyzeRequest in main.py.
    """
    scan_id: str = Field(..., description="ID of the scan to analyze")
    file_url: str = Field(..., description="URL of the scan file to download and analyze")
    user_id: str = Field(..., description="ID of the user requesting the analysis")


class AIChatRequest(BaseModel):
    """
    Schema matching the existing AIChatRequest in main.py.
    """
    message: str = Field(..., description="User message for the AI assistant")
    context: str = Field("", description="Additional context for the AI assistant")


class AuthModel(BaseModel):
    """
    Schema matching the existing AuthModel in routes/auth.py.
    """
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class ResetModel(BaseModel):
    """
    Schema matching the existing ResetModel in routes/auth.py.
    """
    password: str = Field(..., description="New password")
    token: str = Field(..., description="Password reset token")


class GenerateReportRequest(BaseModel):
    """
    Schema matching the existing GenerateReportRequest in routes/reports.py.
    """
    scan_id: str = Field(..., description="ID of the scan to generate a report for")
    patient_email: str = Field("N/A", description="Optional patient email address")
