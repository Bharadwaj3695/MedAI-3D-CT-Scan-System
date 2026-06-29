"""
Admin Routing Module.

This module implements administrative endpoints for fetching all users,
scans, and system statistics. It uses the singleton Supabase client via
dependency injection.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from backend.database import get_supabase
from backend.dependencies import get_current_admin_user
from backend.utils.logger import get_logger

# Initialize logger for the admin router
logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[Dict[str, Any]])
def get_all_users(
    admin_user = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase)
) -> List[Dict[str, Any]]:
    """
    Retrieve all user profiles from the database.
    """
    logger.info("Admin fetching all user profiles.")
    try:
        response = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to fetch user profiles: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/scans", response_model=List[Dict[str, Any]])
def get_all_scans(
    admin_user = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase)
) -> List[Dict[str, Any]]:
    """
    Retrieve the most recent scans across all users.
    """
    logger.info("Admin fetching all scans.")
    try:
        response = supabase.table("scans").select("*, profiles(full_name, email)").order("created_at", desc=True).limit(20).execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to fetch all scans: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats", response_model=Dict[str, int])
def get_admin_stats(
    admin_user = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase)
) -> Dict[str, int]:
    """
    Retrieve aggregate system statistics (total users, total scans, completed scans).
    """
    logger.info("Admin fetching system statistics.")
    try:
        users_resp = supabase.table("profiles").select("*", count="exact").execute()
        scans_resp = supabase.table("scans").select("*", count="exact").execute()
        completed_resp = supabase.table("scans").select("*", count="exact").eq("status", "completed").execute()
        
        return {
            "totalUsers": users_resp.count if (users_resp and hasattr(users_resp, "count")) else 0,
            "totalScans": scans_resp.count if (scans_resp and hasattr(scans_resp, "count")) else 0,
            "completedScans": completed_resp.count if (completed_resp and hasattr(completed_resp, "count")) else 0
        }
    except Exception as e:
        logger.error(f"Failed to fetch admin stats: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
