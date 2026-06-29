"""
Authentication and Authorization Routes.

This module implements the endpoints for user registration, authentication,
session retrieval, and password management. It interfaces with the AuthService
and Supabase to manage user accounts.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from supabase import Client

from backend.database import get_supabase
from backend.dependencies import get_current_user, oauth2_scheme
from backend.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    UserProfile
)
from backend.security import hash_password, verify_password, create_access_token
from backend.services.auth import AuthService
from backend.utils.logger import get_logger

# Initialize logger for the auth router
logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(supabase_client: Client = Depends(get_supabase)) -> AuthService:
    """
    Dependency to retrieve the AuthService instance.
    
    Args:
        supabase_client (Client): The injected Supabase client singleton.
        
    Returns:
        AuthService: An instance of the authentication service.
    """
    return AuthService(supabase_client=supabase_client)


# ==============================================================================
# Local Schemas (for specific route requirements)
# ==============================================================================

class ResetPasswordRequest(BaseModel):
    """
    Schema for password reset requests.
    The token is sent in the Authorization header, so only the password is required in the body.
    """
    password: str = Field(..., min_length=8, description="The new password")


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    supabase_client: Client = Depends(get_supabase)
) -> UserResponse:
    """
    Register a new user in the system.
    
    1. Hashes the user's password using bcrypt.
    2. Registers the user in Supabase Auth (saving the hash in user_metadata).
    3. Creates a default 'user' role for the new user.
    4. Automatically attempts to create a corresponding profile record.
    
    Args:
        data (UserCreate): The registration payload containing email and password.
        auth_service (AuthService): The injected authentication service.
        supabase_client (Client): The injected Supabase client.
        
    Returns:
        UserResponse: The newly created user details.
    """
    logger.info(f"Received signup request for email: {data.email}")
    
    # Hash the password for our local verification
    hashed_pwd = hash_password(data.password)
    
    try:
        # Register user with Supabase Auth
        # We pass the plain password to Supabase so their native auth works,
        # but we also store our custom bcrypt hash in user_metadata.
        auth_res = supabase_client.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "password_hash": hashed_pwd,
                    "full_name": data.email.split("@")[0].capitalize()
                }
            }
        })
        
        if not auth_res or not auth_res.user:
            logger.error("Supabase Auth failed to return a user object.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register user"
            )
            
        user = auth_res.user
        logger.info(f"User successfully registered in Supabase Auth. ID: {user.id}")
        
        # Create profile metadata in the 'profiles' table if required
        try:
            profile_data = {
                "id": user.id,
                "email": user.email,
                "full_name": user.user_metadata.get("full_name"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            supabase_client.table("profiles").insert(profile_data).execute()
            logger.info(f"Profile record created in 'profiles' table for user ID: {user.id}")
        except Exception as profile_err:
            logger.warning(f"Could not create profile record in 'profiles' table: {profile_err}")
            
        # Create default 'user' role in 'user_roles' table
        try:
            supabase_client.table("user_roles").insert({
                "user_id": user.id,
                "role": "user"
            }).execute()
            logger.info(f"Default role 'user' assigned in 'user_roles' table for user ID: {user.id}")
        except Exception as role_err:
            logger.warning(f"Could not assign default role in 'user_roles' table: {role_err}")

        # Parse timestamps safely
        created_at_dt = user.created_at
        if not isinstance(created_at_dt, datetime):
            created_at_dt = datetime.fromisoformat(user.created_at.replace("Z", "+00:00"))
            
        updated_at_dt = None
        if user.updated_at:
            if isinstance(user.updated_at, datetime):
                updated_at_dt = user.updated_at
            else:
                updated_at_dt = datetime.fromisoformat(user.updated_at.replace("Z", "+00:00"))

        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=True,
            profile=UserProfile(
                id=user.id,
                email=user.email,
                full_name=user.user_metadata.get("full_name"),
                avatar_url=user.user_metadata.get("avatar_url"),
                created_at=created_at_dt,
                updated_at=updated_at_dt
            )
        )
        
    except Exception as e:
        logger.error(f"Signup failed for {data.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    supabase_client: Client = Depends(get_supabase)
) -> Token:
    """
    Authenticate a user and issue a JWT access token.
    
    1. Authenticates against Supabase Auth.
    2. Verifies the password using the local bcrypt hash in user_metadata.
    3. Generates and signs a local JWT access token containing the user ID and role.
    
    Args:
        form_data (OAuth2PasswordRequestForm): The login payload containing username (email) and password.
        auth_service (AuthService): The injected authentication service.
        supabase_client (Client): The injected Supabase client.
        
    Returns:
        Token: The JWT access token.
    """
    email = form_data.username
    password = form_data.password

    logger.info(f"Received login request for email: {email}")
    
    try:
        # 1. Authenticate with Supabase Auth (verifies credentials)
        auth_res = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_res or not auth_res.user:
            logger.warning(f"Supabase Auth failed to authenticate: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
        user = auth_res.user
        
        # 2. Verify the password locally using our bcrypt verify_password
        user_metadata = user.user_metadata or {}
        stored_hash = user_metadata.get("password_hash")
        
        if stored_hash:
            if not verify_password(password, stored_hash):
                logger.warning(f"Bcrypt verification failed for user: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
        else:
            logger.info("No bcrypt password_hash found in user_metadata; relying on Supabase auth.")
            
        # Fetch the user's role from 'user_roles' table
        role = "user"
        try:
            role_data = supabase_client.table("user_roles").select("role").eq("user_id", user.id).maybe_single().execute()
            if role_data and role_data.data:
                role = role_data.data.get("role", "user")
        except Exception as role_err:
            logger.warning(f"Could not retrieve role for user {user.id}: {role_err}")
            
        # 3. Generate the local JWT access token
        token_payload = {
            "sub": user.id,
            "email": user.email,
            "role": role
        }
        access_token = create_access_token(data=token_payload)
        
        logger.info(f"Successful login for user: {email}. Token generated.")
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login process failed for {email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.get("/me")
def get_me(
    current_user: Any = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase)
) -> Dict[str, Any]:
    """
    Retrieve the details and role of the currently authenticated user.
    
    Args:
        current_user (Any): The authenticated user injected via get_current_user.
        supabase_client (Client): The injected Supabase client.
        
    Returns:
        Dict[str, Any]: The user details and their assigned role.
    """
    logger.info(f"Fetching /me profile for user ID: {current_user.id}")
    
    # Retrieve user's role
    role = "user"
    try:
        role_data = supabase_client.table("user_roles").select("role").eq("user_id", current_user.id).maybe_single().execute()
        if role_data and role_data.data:
            role = role_data.data.get("role", "user")
    except Exception as e:
        logger.warning(f"Failed to fetch role for user {current_user.id}: {e}")
        
    # Serialize the user model to dictionary
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "user_metadata": current_user.user_metadata or {},
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }
    
    return {
        "user": user_dict,
        "role": role
    }


@router.post("/logout")
def logout() -> Dict[str, str]:
    """
    Log out the current user session.
    
    JWT Logout Behavior (Stateless):
    JWTs are stateless credentials stored on the client. To 'log out', the client
    simply discards/deletes the token from local storage. The server does not maintain
    session state for JWTs, making this endpoint stateless. We return a success message
    confirming the logout action.
    
    Returns:
        Dict[str, str]: Status and logout confirmation message.
    """
    logger.info("Stateless logout endpoint triggered.")
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/google")
def google_auth(auth_service: AuthService = Depends(get_auth_service)) -> Dict[str, str]:
    """
    Generate and return the Google OAuth authorization URL.
    
    Args:
        auth_service (AuthService): The injected authentication service.
        
    Returns:
        Dict[str, str]: Dict containing the redirect URL.
    """
    logger.info("Generating Google OAuth authorization URL.")
    try:
        url = auth_service.get_oauth_url(provider="google")
        return {"url": url}
    except Exception as e:
        logger.error(f"Failed to generate Google OAuth URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Reset the password for the currently authenticated user.
    
    Args:
        data (ResetPasswordRequest): The payload containing the new password.
        token (str): The authenticated user's token from the Authorization header.
        auth_service (AuthService): The injected authentication service.
        
    Returns:
        Dict[str, Any]: Status and confirmation message.
    """
    logger.info("Received request to reset password.")
    try:
        return auth_service.reset_password(password=data.password, token=token)
    except Exception as e:
        logger.error(f"Password reset failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
