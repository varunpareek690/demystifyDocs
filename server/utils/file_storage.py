import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from core.config import settings

class LocalFileStorage:
    """Handle local file storage operations."""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        self.ensure_upload_directory()
    
    def ensure_upload_directory(self):
        """Create upload directory if it doesn't exist."""
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        (self.upload_dir / "documents").mkdir(exist_ok=True)
        (self.upload_dir / "temp").mkdir(exist_ok=True)
    
    def get_user_directory(self, user_id: str) -> Path:
        """Get or create user-specific directory."""
        user_dir = self.upload_dir / "documents" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    async def save_file(self, file: UploadFile, user_id: str, custom_filename: Optional[str] = None) -> dict:
        """Save uploaded file to local storage."""
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            original_filename = file.filename or "unknown"
            file_extension = os.path.splitext(original_filename)[1].lower()
            
            # Use custom filename or generate one
            if custom_filename:
                # Ensure custom filename has proper extension
                if not custom_filename.endswith(file_extension):
                    stored_filename = f"{custom_filename}{file_extension}"
                else:
                    stored_filename = custom_filename
            else:
                stored_filename = f"{file_id}_{original_filename}"
            
            # Get user directory
            user_dir = self.get_user_directory(user_id)
            file_path = user_dir / stored_filename
            
            # Ensure unique filename
            counter = 1
            base_name = stored_filename
            while file_path.exists():
                name, ext = os.path.splitext(base_name)
                stored_filename = f"{name}_{counter}{ext}"
                file_path = user_dir / stored_filename
                counter += 1
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file info
            file_size = file_path.stat().st_size
            
            return {
                "file_id": file_id,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "file_path": str(file_path),
                "relative_path": str(file_path.relative_to(self.upload_dir)),
                "file_size": file_size,
                "file_extension": file_extension
            }
            
        except Exception as e:
            raise Exception(f"Error saving file: {str(e)}")
    
    def get_file_path(self, user_id: str, filename: str) -> Path:
        """Get full path to a user's file."""
        user_dir = self.get_user_directory(user_id)
        return user_dir / filename
    
    def delete_file(self, user_id: str, filename: str) -> bool:
        """Delete a user's file."""
        try:
            file_path = self.get_file_path(user_id, filename)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, user_id: str, filename: str) -> bool:
        """Check if a user's file exists."""
        file_path = self.get_file_path(user_id, filename)
        return file_path.exists()
    
    def get_file_size(self, user_id: str, filename: str) -> Optional[int]:
        """Get file size."""
        try:
            file_path = self.get_file_path(user_id, filename)
            if file_path.exists():
                return file_path.stat().st_size
            return None
        except Exception:
            return None
