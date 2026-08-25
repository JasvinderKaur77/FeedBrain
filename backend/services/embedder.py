from fastembed import TextEmbedding
from db.qdrant_client import get_qdrant, COLLECTION_NAME
from qdrant_client.models import PointStruct
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize embedding model once
embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")

def generate_embedding(text: str) -> list:
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()

def store_embedding(save_id: str, text: str, metadata: dict) -> str:
    qdrant = get_qdrant()
    
    embedding = generate_embedding(text)
    point_id = str(uuid.uuid4())
    
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "save_id": save_id,
                    "user_id": metadata.get("user_id"),
                    "title": metadata.get("title"),
                    "source_type": metadata.get("source_type"),
                    "tags": metadata.get("tags", [])
                }
            )
        ]
    )
    
    return point_id

def search_embeddings(query: str, user_id: str, limit: int = 5) -> list:
    qdrant = get_qdrant()
    
    query_embedding = generate_embedding(query)
    
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=limit,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
        )
    )
    
    return results.points