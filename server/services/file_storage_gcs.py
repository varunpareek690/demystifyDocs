import uuid
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError
from fastapi import UploadFile
from core.config import settings
from utils.exceptions import FileProcessingError, ServiceUnavailableError

class GCSFileStorage:
    """Google Cloud Storage file management service."""
    
    def __init__(self):
        """Initialize GCS client with service account credentials."""
        try:
            # Initialize GCS client - uses service account from env
            self.client = storage.Client(project=settings.GCP_PROJECT_ID)
            self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
        except Exception as e:
            raise ServiceUnavailableError(f"Storage service unavailable: {str(e)}")

    async def save_file(self, file: UploadFile, user_id: str, custom_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Save uploaded file to GCS bucket.
        
        Args:
            file: FastAPI UploadFile object
            user_id: User ID for organizing files
            custom_title: Optional custom title for the file
            
        Returns:
            Dict with file metadata
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename or "")
            unique_id = str(uuid.uuid4())
            stored_filename = f"{unique_id}{file_extension}"
            
            # Create GCS object path: users/{user_id}/documents/{stored_filename}
            blob_path = f"users/{user_id}/documents/{stored_filename}"
            
            # Upload to GCS
            blob = self.bucket.blob(blob_path)
            
            # Set metadata
            blob.metadata = {
                'user_id': user_id,
                'original_filename': file.filename or 'unknown',
                'custom_title': custom_title or '',
                'uploaded_at': datetime.utcnow().isoformat(),
                'file_type': file_extension
            }
            
            # Upload file content
            file_content = await file.read()
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: blob.upload_from_string(
                    file_content,
                    content_type=file.content_type or 'application/octet-stream'
                )
            )
            
            # Reset file pointer for potential reuse
            await file.seek(0)
                        
            return {
                'blob_path': blob_path,
                'stored_filename': stored_filename,
                'original_filename': file.filename or 'unknown',
                'file_size': len(file_content),
                'content_type': file.content_type,
                'gcs_url': f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"
            }
            
        except Exception as e:
            raise FileProcessingError(f"File upload failed: {str(e)}")

    async def get_file_content(self, blob_path: str, user_id: str) -> bytes:
        """
        Retrieve file content from GCS.
        
        Args:
            blob_path: GCS blob path
            user_id: User ID for security check
            
        Returns:
            File content as bytes
        """
        try:
            blob = self.bucket.blob(blob_path)
            
            # Security check: ensure blob belongs to user
            if not blob_path.startswith(f"users/{user_id}/"):
                raise FileProcessingError("Access denied to file")
            
            # Check if file exists
            if not await asyncio.get_event_loop().run_in_executor(None, blob.exists):
                raise FileProcessingError("File not found")
            
            # Download file content
            content = await asyncio.get_event_loop().run_in_executor(
                None, blob.download_as_bytes
            )
            
            return content
            
        except NotFound:
            raise FileProcessingError("File not found")
        except GoogleCloudError as e:
            raise ServiceUnavailableError(f"Storage service error: {str(e)}")
        except Exception as e:
            raise FileProcessingError(f"Failed to retrieve file: {str(e)}")

    async def delete_file(self, blob_path: str, user_id: str) -> bool:
        """
        Delete file from GCS.
        
        Args:
            blob_path: GCS blob path
            user_id: User ID for security check
            
        Returns:
            True if deleted successfully
        """
        try:
            blob = self.bucket.blob(blob_path)
            
            if not blob_path.startswith(f"users/{user_id}/"):
                raise FileProcessingError("Access denied to file")
            await asyncio.get_event_loop().run_in_executor(None, blob.delete)
            return True
            
        except NotFound:
            return True
        except GoogleCloudError as e:
            raise ServiceUnavailableError(f"Storage service error: {str(e)}")
        except Exception as e:
            raise FileProcessingError(f"Failed to delete file: {str(e)}")

    async def generate_signed_url(self, blob_path: str, user_id: str, expiration_minutes: int = 60) -> str:
        """
        Generate a signed URL for temporary file access.
        
        Args:
            blob_path: GCS blob path
            user_id: User ID for security check
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Signed URL string
        """
        try:
            blob = self.bucket.blob(blob_path)
            
            # Security check: ensure blob belongs to user
            if not blob_path.startswith(f"users/{user_id}/"):
                raise FileProcessingError("Access denied to file")
            
            # Generate signed URL
            expiration_time = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            signed_url = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: blob.generate_signed_url(
                    expiration=expiration_time,
                    method='GET'
                )
            )
            
            return signed_url
            
        except Exception as e:
            raise FileProcessingError(f"Failed to generate download URL: {str(e)}")

    async def list_user_files(self, user_id: str, limit: int = 100) -> list:
        """
        List all files for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata
        """
        try:
            prefix = f"users/{user_id}/documents/"
            
            blobs = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self.client.list_blobs(
                    self.bucket, 
                    prefix=prefix, 
                    max_results=limit
                ))
            )
            
            files = []
            for blob in blobs:
                files.append({
                    'blob_path': blob.name,
                    'size': blob.size,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'content_type': blob.content_type,
                    'metadata': blob.metadata or {}
                })
            
            return files
            
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to list files: {str(e)}")

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file against size and extension limits."""
    
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise FileProcessingError(
                f"File size ({file_size} bytes) exceeds maximum allowed size ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        if file.filename:
            file_extension = self._get_file_extension(file.filename)
            if file_extension.lower() not in settings.ALLOWED_EXTENSIONS:
                raise FileProcessingError(
                    f"File type '{file_extension}' not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                )

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''

    async def cleanup_orphaned_files(self, user_id: str, valid_blob_paths: list) -> int:
        """
        Clean up orphaned files that are not referenced in the database.
        
        Args:
            user_id: User ID
            valid_blob_paths: List of blob paths that should be kept
            
        Returns:
            Number of files deleted
        """
        try:
            all_files = await self.list_user_files(user_id)
            deleted_count = 0
            
            for file_info in all_files:
                if file_info['blob_path'] not in valid_blob_paths:
                    try:
                        await self.delete_file(file_info['blob_path'], user_id)
                        deleted_count += 1
                    except Exception:
                        pass
            
            return deleted_count
            
        except Exception:
            return 0