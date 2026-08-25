from services.embedder import search_embeddings
from db.supabase_client import get_supabase

def get_digest_saves(user_id: str, limit: int = 3) -> list:
    try:
        supabase = get_supabase()
        
        # Get user's most recent saves
        recent = supabase.table("saves")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        if not recent.data:
            return []
        
        # Build a query from recent tags and summaries
        recent_tags = []
        for save in recent.data[:3]:
            if save.get("tags"):
                recent_tags.extend(save["tags"])
        
        if not recent_tags:
            return recent.data[:3]
        
        # Search for semantically related saves
        query = " ".join(set(recent_tags[:10]))
        results = search_embeddings(
            query=query,
            user_id=user_id,
            limit=limit + 3
        )
        
        if not results:
            return recent.data[:limit]
        
        # Get full save details from Supabase
        digest_saves = []
        seen_ids = set()
        
        for hit in results:
            save_id = hit.payload.get("save_id")
            if save_id and save_id not in seen_ids:
                save = supabase.table("saves")\
                    .select("*")\
                    .eq("id", save_id)\
                    .execute()
                if save.data:
                    digest_saves.append({
                        "save": save.data[0],
                        "reason": f"Related to your recent saves about {', '.join(recent_tags[:3])}"
                    })
                    seen_ids.add(save_id)
            
            if len(digest_saves) >= limit:
                break
        
        return digest_saves
        
    except Exception as e:
        print(f"Resurfacer error: {str(e)}")
        return []