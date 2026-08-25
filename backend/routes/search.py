from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.embedder import search_embeddings
from db.supabase_client import get_supabase

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    user_id: str
    limit: int = 5

@router.post("/search")
async def search_saves(request: SearchRequest):
    try:
        # Step 1 — Search Qdrant by meaning
        qdrant_results = search_embeddings(
            query=request.query,
            user_id=request.user_id,
            limit=request.limit
        )

        if not qdrant_results:
            return {"results": [], "message": "No relevant saves found"}

        # Step 2 — Get full details from Supabase
        supabase = get_supabase()
        results = []

        for hit in qdrant_results:
            save_id = hit.payload.get("save_id")
            score = hit.score

            save = supabase.table("saves")\
                .select("*")\
                .eq("id", save_id)\
                .execute()

            if save.data:
                item = save.data[0]
                item["relevance_score"] = round(score, 3)
                item["relevance_reason"] = f"Matched with {round(score * 100)}% relevance"
                results.append(item)

        return {
            "query": request.query,
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")