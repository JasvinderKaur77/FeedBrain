from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.extractor import extract_content
from services.summariser import summarise_content
from services.embedder import store_embedding
from db.supabase_client import get_supabase
import uuid

router = APIRouter()

class SaveRequest(BaseModel):
    url: str
    user_id: str
    annotation: str = ""  # for Instagram reels

@router.post("/save")
async def save_url(request: SaveRequest):
    try:
        # Step 1 — Extract content
        extracted = extract_content(request.url)
        
        if not extracted:
            raise HTTPException(status_code=400, detail="Could not extract content from URL")
        
        # Step 2 — If Instagram, use annotation as content
        if extracted.get("source_type") == "instagram" and request.annotation:
            extracted["content"] = request.annotation
        
        # Step 3 — Summarise
        if extracted.get("content"):
            summarised = summarise_content(
                title=extracted.get("title", "Untitled"),
                content=extracted["content"],
                source_type=extracted.get("source_type", "article")
            )
        else:
            summarised = {
                "summary": ["Content could not be extracted", "URL has been saved", "Try adding a manual note"],
                "tags": ["uncategorised"]
            }
        
        # Step 4 — Store in Supabase
        supabase = get_supabase()
        save_data = {
            "user_id": request.user_id,
            "url": request.url,
            "title": extracted.get("title", "Untitled"),
            "source_type": extracted.get("source_type", "other"),
            "summary": summarised["summary"],
            "tags": summarised["tags"],
            "raw_content": extracted.get("content", "")[:5000],
        }
        
        result = supabase.table("saves").insert(save_data).execute()
        save_id = result.data[0]["id"]
        
        # Step 5 — Store embedding in Qdrant
        text_to_embed = " ".join(summarised["summary"]) + " " + " ".join(summarised["tags"])
        qdrant_id = store_embedding(
            save_id=save_id,
            text=text_to_embed,
            metadata={
                "user_id": request.user_id,
                "title": extracted.get("title", "Untitled"),
                "source_type": extracted.get("source_type", "other"),
                "tags": summarised["tags"]
            }
        )
        
        # Step 6 — Update Supabase with qdrant_id
        supabase.table("saves").update({"qdrant_id": qdrant_id}).eq("id", save_id).execute()
        
        return {
            "id": save_id,
            "title": extracted.get("title", "Untitled"),
            "source_type": extracted.get("source_type", "other"),
            "summary": summarised["summary"],
            "tags": summarised["tags"],
            "url": request.url,
            "message": "Saved successfully 🧠"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving content: {str(e)}")

@router.get("/saves")
async def get_saves(user_id: str):
    try:
        supabase = get_supabase()
        result = supabase.table("saves")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        
        return {
            "saves": result.data,
            "total": len(result.data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching saves: {str(e)}"
        )

@router.delete("/saves/{save_id}")
async def delete_save(save_id: str, user_id: str):
    try:
        supabase = get_supabase()
        
        # Get qdrant_id first
        save = supabase.table("saves")\
            .select("qdrant_id")\
            .eq("id", save_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not save.data:
            raise HTTPException(status_code=404, detail="Save not found")
        
        # Delete from Supabase
        supabase.table("saves")\
            .delete()\
            .eq("id", save_id)\
            .eq("user_id", user_id)\
            .execute()
        
        return {"message": "Deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))