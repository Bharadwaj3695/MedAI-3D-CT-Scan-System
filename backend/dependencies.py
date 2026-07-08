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

from .database import get_supabase
from .security import verify_token
from .utils.logger import get_logger

# Initialize logger for the dependencies module
logger = get_logger(__name__)

# Define OAuth2 scheme for extracting JWT tokens from the Authorization header.
# tokenUrl points to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==============================================================================
# Authentication Dependencies
# ==============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    supabase_client: Client = Depends(get_supabase)
) -> Any:
    """
    Dependency to get the currently authenticated user.
    
    Extracts the JWT token from the Authorization header, validates it using
    the security helper, and retrieves the corresponding user from Supabase.
    
    Args:
        token (str): The JWT token extracted from the Authorization header.
        supabase_client (Client): The injected Supabase client.
        
    Returns:
        Any: The Supabase user object.
        
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
    
    # 2. Retrieve the user from Supabase using the token
    try:
        user_resp = supabase_client.auth.get_user(token)
        if not user_resp or not user_resp.user:
            logger.warning("User not found in Supabase for the provided token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"User {user_resp.user.id} authenticated successfully.")
        return user_resp.user
    except Exception as e:
        logger.error(f"Failed to retrieve user from Supabase: {e}", exc_info=True)
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
    supabase_client: Client = Depends(get_supabase)
) -> Dict[str, Any]:
    """
    Dependency to verify if the authenticated user has an 'admin' role.
    
    Queries the 'user_roles' table in Supabase to verify user permissions.
    
    Args:
        current_user (Any): The active authenticated user.
        supabase_client (Client): The injected Supabase client.
        
    Returns:
        Dict[str, Any]: A dictionary containing the user object and their role.
        
    Raises:
        HTTPException: 403 Forbidden if the user is not an admin.
    """
    user_id = current_user.id
    logger.info(f"Verifying admin privileges for user {user_id}.")
    
    try:
        role_data = supabase_client.table("user_roles").select("role").eq("user_id", user_id).maybe_single().execute()
        
        if role_data and role_data.data:
            role = role_data.data.get("role", "user")
            if role == "admin":
                logger.info(f"User {user_id} verified as admin.")
                return {"user": current_user, "role": role}
                
        logger.warning(f"User {user_id} is not authorized as an admin.")
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
