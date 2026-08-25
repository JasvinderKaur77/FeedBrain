from fastapi import APIRouter, HTTPException
from services.resurfacer import get_digest_saves

router = APIRouter()

@router.get("/digest")
async def get_digest(user_id: str):
    try:
        resurfaces = get_digest_saves(user_id=user_id, limit=3)
        
        return {
            "user_id": user_id,
            "resurfaces": resurfaces,
            "total": len(resurfaces),
            "message": "Your daily resurfaces 🧠"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Digest error: {str(e)}"
        )