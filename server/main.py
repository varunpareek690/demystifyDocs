import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.router import api_router
from core.config import settings
from core.firebase_config import initialize_firebase

app = FastAPI(
    title="Legal AI Backend",
    description="AI solution for simplifying legal documents",
    version="1.0.0",
)

@app.on_event("startup")
def on_startup():
    """Initializes directories and services when the app starts."""
    print("🚀 Starting up...")
    try:
        initialize_firebase()
        print("✓ Firebase initialized")
    except Exception as e:
        print(f"✗ Firebase initialization failed: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Server Health"])
def root():
    """A simple health check endpoint."""
    return {"message": "Legal AI Backend is running"}