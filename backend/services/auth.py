from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from backend.services.base import BaseService
from backend.security import create_access_token
import requests

class AuthService(BaseService):
    """
    Service to handle user authentication, registrations, sessions,
    and password resets, interfacing with Supabase Auth or a local DB.
    """

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        """
        if not self.supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Database/Authentication service is disabled"
            )
        try:
            response = self.supabase.auth.sign_up({"email": email, "password": password})
            return response.model_dump()
        except Exception as e:
            self.logger.error(f"Sign up failed for {email}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and return session details.
        """
        if not self.supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Database/Authentication service is disabled"
            )
        try:
            response = self.supabase.auth.sign_in_with_password({"email": email, "password": password})
            return response.model_dump()
        except Exception as e:
            self.logger.error(f"Sign in failed for {email}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def sign_out(self) -> None:
        """
        Log out the current user session.
        """
        if not self.supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Database/Authentication service is disabled"
            )
        try:
            self.supabase.auth.sign_out()
        except Exception as e:
            self.logger.error(f"Sign out failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_oauth_url(self, provider: str = "google", redirect_to: str = "http://127.0.0.1:8000/dashboard") -> str:
        """
        Generate OAuth authorization URL.
        """
        if not self.supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Database/Authentication service is disabled"
            )
        try:
            res = self.supabase.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {"redirect_to": redirect_to}
            })
            return res.url
        except Exception as e:
            self.logger.error(f"OAuth failed for {provider}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_user_role(self, user_id: str) -> str:
        """
        Retrieve the role of the user. Defaults to 'user'.
        """
        if not self.supabase:
            return "user"
        try:
            role_data = self.supabase.table("user_roles").select("role").eq("user_id", user_id).maybe_single().execute()
            if role_data and role_data.data:
                return role_data.data.get("role", "user")
        except Exception as e:
            self.logger.warning(f"Failed to fetch role for user {user_id}: {str(e)}")
        return "user"

    def reset_password(self, password: str, token: str) -> Dict[str, Any]:
        """
        Update the password for the currently authenticated user session.
        """
        if not self.supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Database/Authentication service is disabled"
            )
        try:
            headers = {
                "apikey": self.supabase.table("dummy")._client.supabase_key, # access the key
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            res = requests.put(
                f"{self.supabase.table('dummy')._client.supabase_url}/auth/v1/user", 
                headers=headers, 
                json={"password": password}
            )
            res.raise_for_status()
            return {"status": "success", "message": "Password updated successfully"}
        except requests.exceptions.RequestException as e:
            detail = e.response.text if e.response else str(e)
            self.logger.error(f"Password reset request failed: {detail}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to reset password: {detail}")
        except Exception as e:
            self.logger.error(f"Password reset failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
