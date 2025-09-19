from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from api.v1.router import api_router
from core.firebase_config import initialize_firebase

def create_application() -> FastAPI:
    """Create FastAPI application with all configurations."""
    application = FastAPI(
        title="Legal AI Backend",
        description="AI solution for simplifying legal documents",
        version="1.0.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    initialize_firebase()

    # application.include_router(api_router, prefix="/api/v1")

    return application

app = create_application()

@app.get("/")
async def root(): 
    return {"message": "Legal AI Backend API", "version": "1.0.0"}