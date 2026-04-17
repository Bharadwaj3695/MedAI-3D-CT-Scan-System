from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.supabase_client import supabase
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

class AuthModel(BaseModel):
    email: str
    password: str

@router.post("/signup")
def signup(data: AuthModel):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    try:
        response = supabase.auth.sign_up({"email": data.email, "password": data.password})
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(data: AuthModel):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    try:
        response = supabase.auth.sign_in_with_password({"email": data.email, "password": data.password})
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
def logout():
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    try:
        supabase.auth.sign_out()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/google")
def google_auth():
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    try:
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": "http://127.0.0.1:8000/dashboard"}
        })
        return {"url": res.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    token = credentials.credentials
    try:
        user_resp = supabase.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        user_id = user_resp.user.id
        role = "user"
        try:
            role_data = supabase.table("user_roles").select("role").eq("user_id", user_id).maybe_single().execute()
            if role_data and role_data.data:
                role = role_data.data.get("role", "user")
        except:
            pass
            
        return {"user": user_resp.user.model_dump(), "role": role}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database disabled")
    token = credentials.credentials
    try:
        user_resp = supabase.auth.get_user(token)
        return user_resp.user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid auth credentials")
