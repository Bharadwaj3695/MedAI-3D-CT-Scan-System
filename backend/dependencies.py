"""
FastAPI Dependency Injection Module.

This module defines reusable dependencies for route handlers, including:
1. User authentication and JWT token validation.
2. Active user verification.
3. Role-based access control (Admin privilege checks).
4. Database session providers.
"""

import logging
from typing import Any, Dict, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import Client

from backend.database import get_db, get_supabase
from backend.security import verify_token
from backend.utils.logger import get_logger

# Initialize logger for the dependencies module
logger = get_logger(__name__)

# Define OAuth2 scheme for extracting JWT tokens from the Authorization header.
# tokenUrl points to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==============================================================================
# Authentication Dependencies
# ==============================================================================

class UserProfileCompat:
    """
    A compatibility class that mimics the Supabase User object
    for routes and dependencies that expect a User model.
    """
    def __init__(self, profile_data: dict):
        self.id = str(profile_data.get("id"))
        self.email = profile_data.get("email")
        self.created_at = profile_data.get("created_at")
        self.updated_at = profile_data.get("updated_at")
        self.user_metadata = {
            "full_name": profile_data.get("full_name"),
            "avatar_url": profile_data.get("avatar_url"),
            "disabled": profile_data.get("disabled", False),
            "inactive": profile_data.get("inactive", False),
        }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    supabase_client: Client = Depends(get_supabase)
) -> Any:
    """
    Dependency to get the currently authenticated user.
    
    Extracts the JWT token from the Authorization header, validates it using
    the security helper, and retrieves the corresponding user from the database.
    
    Args:
        token (str): The JWT token extracted from the Authorization header.
        supabase_client (Client): The injected Supabase client.
        
    Returns:
        Any: The compatible user profile object.
        
    Raises:
        HTTPException: 401 Unauthorized if token is invalid, expired, or user not found.
    """
    logger.info("Authenticating user via JWT token.")
    
    # 1. Verify the token using security.py
    payload = verify_token(token)
    if not payload:
        logger.warning("Token verification failed or token expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Retrieve the user from the 'profiles' table using the user ID (sub claim)
    try:
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT token is missing the 'sub' claim.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        profile_resp = supabase_client.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
        if not profile_resp or not profile_resp.data:
            logger.warning(f"User profile not found in database for ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        profile_data = profile_resp.data
        logger.info(f"User {user_id} authenticated successfully.")
        return UserProfileCompat(profile_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve user profile from database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Dependency to ensure the authenticated user is active.
    
    Checks user metadata or status to verify they are not disabled or suspended.
    
    Args:
        current_user (Any): The authenticated user object from get_current_user.
        
    Returns:
        Any: The active user object.
        
    Raises:
        HTTPException: 401 Unauthorized if the user account is disabled/inactive.
    """
    logger.info(f"Checking active status for user {current_user.id}.")
    
    # Inspect user metadata for any 'disabled' or 'inactive' flags.
    user_metadata = getattr(current_user, "user_metadata", {}) or {}
    if user_metadata.get("disabled", False) or user_metadata.get("inactive", False):
        logger.warning(f"User {current_user.id} is marked as inactive/disabled.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
        
    return current_user


def get_current_admin_user(
    current_user: Any = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
    supabase_client: Client = Depends(get_supabase)
) -> Dict[str, Any]:
    """
    Dependency to verify if the authenticated user has an 'admin' role.
    
    First checks the role claim in the JWT token. If not found, falls back
    to querying the 'user_roles' table in Supabase.
    
    Args:
        current_user (Any): The active authenticated user.
        token (str): The JWT token.
        supabase_client (Client): The injected Supabase client.
        
    Returns:
        Dict[str, Any]: A dictionary containing the user object and their role.
        
    Raises:
        HTTPException: 403 Forbidden if the user is not an admin.
    """
    user_id = current_user.id
    logger.info(f"Verifying admin privileges for user {user_id}.")
    
    # 1. Try to get the role from the JWT token first (fast path)
    payload = verify_token(token)
    if payload:
        role = payload.get("role")
        if role == "admin":
            logger.info(f"User {user_id} verified as admin via JWT.")
            return {"user": current_user, "role": role}
        elif role == "user":
            # If the token explicitly says 'user', we can trust it and deny access
            logger.warning(f"User {user_id} is not authorized as an admin (Role: user in JWT).")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have enough privileges"
            )

    # 2. Fallback to database query if role is not in JWT (e.g. Supabase native tokens)
    logger.info(f"Role not found in JWT or token invalid. Querying database for user {user_id}.")
    try:
        role_data = supabase_client.table("user_roles").select("role").eq("user_id", user_id).maybe_single().execute()
        
        if role_data and role_data.data:
            role = role_data.data.get("role", "user")
            if role == "admin":
                logger.info(f"User {user_id} verified as admin via database.")
                return {"user": current_user, "role": role}
                
        logger.warning(f"User {user_id} is not authorized as an admin (database check).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during admin privilege check for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Privilege check failed: {str(e)}"
        )


# ==============================================================================
# Legacy Compatibility Helpers
# ==============================================================================

def get_current_user_id(
    current_user: Any = Depends(get_current_user)
) -> str:
    """
    Legacy helper to get the current authenticated user's ID.
    Preserved for backwards compatibility.
    
    Args:
        current_user (Any): The authenticated user object.
        
    Returns:
        str: The user ID.
    """
    return str(current_user.id)
