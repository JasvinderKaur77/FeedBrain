from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from db.supabase_client import get_supabase
from db.qdrant_client import init_collection
import os
from routes.save import router as save_router
from routes.search import router as search_router
from routes.digest import router as digest_router
from routes.auth import router as auth_router

load_dotenv()

app = FastAPI(
    title="FeedBrain API",
    description="Backend for FeedBrain - save anything, forget nothing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(save_router)
app.include_router(search_router)
app.include_router(digest_router)
app.include_router(auth_router)

@app.on_event("startup")
async def startup_event():
    print("🧠 FeedBrain starting up...")
    init_collection()
    print("✅ All systems connected")

@app.get("/")
def root():
    return {"status": "FeedBrain backend is live 🧠"}

@app.get("/health")
def health():
    supabase = get_supabase()
    return {
        "status": "healthy",
        "supabase": "connected",
        "qdrant": "connected"
    }