import uuid
import os
import aiofiles
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile

from core.config import settings # Assuming you'll add LOCAL_STORAGE_PATH here
from utils.exceptions import FileProcessingError, ServiceUnavailableError

class LocalFileStorage:
    """Local filesystem file management service."""

    def __init__(self):
        """Initialize local storage, ensuring the base directory exists."""
        try:
            # It's good practice to define this in your settings
            self.base_path = Path(settings.LOCAL_STORAGE_PATH)
            os.makedirs(self.base_path, exist_ok=True)
        except Exception as e:
            raise ServiceUnavailableError(f"Local storage unavailable: {str(e)}")

    async def save_file(self, file: UploadFile, user_id: str, custom_title: Optional[str] = None) -> Dict[str, Any]:
        """Save uploaded file to the local filesystem."""
        try:
            await self._validate_file(file)

            file_extension = self._get_file_extension(file.filename or "")
            unique_id = str(uuid.uuid4())
            stored_filename = f"{unique_id}{file_extension}"

            # Create local file path: {base_path}/users/{user_id}/documents/{stored_filename}
            user_dir = self.base_path / "users" / user_id / "documents"
            os.makedirs(user_dir, exist_ok=True)
            file_path = user_dir / stored_filename
            relative_path = file_path.relative_to(self.base_path)

            # Write file content asynchronously
            file_content = await file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)

            await file.seek(0)

            return {
                'blob_path': str(relative_path), # Using 'blob_path' for compatibility
                'stored_filename': stored_filename,
                'original_filename': file.filename or 'unknown',
                'file_size': len(file_content),
                'content_type': file.content_type,
                'gcs_url': None # No GCS URL for local files
            }
        except Exception as e:
            raise FileProcessingError(f"File upload failed: {str(e)}")

    async def get_file_content(self, blob_path: str, user_id: str) -> bytes:
        """Retrieve file content from the local filesystem."""
        try:
            # Security check
            if not blob_path.startswith(f"users/{user_id}/"):
                raise FileProcessingError("Access denied to file")

            file_path = self.base_path / blob_path
            if not file_path.is_file():
                raise FileProcessingError("File not found")

            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()

        except FileNotFoundError:
            raise FileProcessingError("File not found")
        except Exception as e:
            raise FileProcessingError(f"Failed to retrieve file: {str(e)}")

    async def delete_file(self, blob_path: str, user_id: str) -> bool:
        """Delete file from the local filesystem."""
        try:
            if not blob_path.startswith(f"users/{user_id}/"):
                raise FileProcessingError("Access denied to file")

            file_path = self.base_path / blob_path
            
            # Use run_in_executor for the blocking os.remove call
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, os.remove, file_path)
            return True

        except FileNotFoundError:
            return True # File is already gone, so the goal is achieved
        except Exception as e:
            raise FileProcessingError(f"Failed to delete file: {str(e)}")

    async def generate_signed_url(self, blob_path: str, user_id: str, expiration_minutes: int = 60) -> str:
        """
        Generate a local URL path for file access.
        NOTE: This is not a 'signed' URL. It returns a predictable path.
        You will need a separate endpoint to serve files from this path.
        """
        if not blob_path.startswith(f"users/{user_id}/"):
            raise FileProcessingError("Access denied to file")
            
        return f"/api/v1/files/{blob_path}"

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file against size and extension limits."""
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)
        if file_size > settings.MAX_FILE_SIZE:
            raise FileProcessingError(f"File size exceeds maximum allowed size")
        if file.filename:
            file_extension = self._get_file_extension(file.filename)
            if file_extension.lower() not in settings.ALLOWED_EXTENSIONS:
                raise FileProcessingError(f"File type '{file_extension}' not allowed.")

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''