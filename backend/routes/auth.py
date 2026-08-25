from fastapi import APIRouter, HTTPException
from db.supabase_client import get_supabase
from pydantic import BaseModel

router = APIRouter()

class AuthRequest(BaseModel):
    email: str
    password: str

@router.post("/auth/signup")
async def signup(request: AuthRequest):
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        
        if response.user:
            # Create user record in our users table
            supabase.table("users").upsert({
                "id": response.user.id,
                "email": response.user.email
            }).execute()
            
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "message": "Account created successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Signup failed")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/login")
async def login(request: AuthRequest):
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token,
                "message": "Logged in successfully"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/auth/google")
async def google_auth(token: str):
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_id_token({
            "provider": "google",
            "token": token
        })
        
        if response.user:
            supabase.table("users").upsert({
                "id": response.user.id,
                "email": response.user.email
            }).execute()
            
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token,
                "message": "Google login successful"
            }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/auth/me")
async def get_me(access_token: str):
    try:
        supabase = get_supabase()
        response = supabase.auth.get_user(access_token)
        
        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))