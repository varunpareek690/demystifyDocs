from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings with GCS and Vertex AI configuration."""
    
    # Basic app settings
    FRONTEND_URL: str = "http://localhost:4200"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:4200", "http://10.238.216.115:4200"]
    
    # Google Cloud Platform settings
    GCP_PROJECT_ID: str
    GOOGLE_APPLICATION_CREDENTIALS: str  # Path to service account JSON or JSON string
    
    # Google Cloud Storage settings
    GCS_BUCKET_NAME: str
    GCS_REGION: str = "us-central1"
    
    # Vertex AI settings
    VERTEX_AI_LOCATION: str = "us-central1"
    VERTEX_MAX_TOKENS: int = 8000  # Conservative limit for text processing
    
    # OAuth settings (keep existing)
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:4200"
    
    # Firebase settings (keep existing for Firestore)
    FIREBASE_PROJECT_ID: str  # Should match GCP_PROJECT_ID
    FIREBASE_PRIVATE_KEY_ID: str
    FIREBASE_PRIVATE_KEY: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_CLIENT_ID: str
    FIREBASE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    
    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".doc", ".txt"}
    
    # Chunking and AI processing settings
    DEFAULT_CHUNK_SIZE: int = 3000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_FOR_CHAT: int = 5
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set up Google Application Credentials if not already set
        if self.GOOGLE_APPLICATION_CREDENTIALS:
            if os.path.isfile(self.GOOGLE_APPLICATION_CREDENTIALS):
                # It's a file path
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.GOOGLE_APPLICATION_CREDENTIALS
            else:
                # It might be JSON content as string - write to temp file
                import tempfile
                import json
                try:
                    # Try to parse as JSON
                    cred_dict = json.loads(self.GOOGLE_APPLICATION_CREDENTIALS)
                    # Write to temporary file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(cred_dict, f)
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
                except json.JSONDecodeError:
                    # Assume it's already a file path
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.GOOGLE_APPLICATION_CREDENTIALS

settings = Settings()