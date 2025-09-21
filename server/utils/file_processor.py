import os
import asyncio
from typing import Tuple
from fastapi import UploadFile
from core.config import settings
from utils.exceptions import FileProcessingError


class FileProcessor:
    """Utilities for processing uploaded files and extracting text content."""
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """
        Validate uploaded file meets requirements.
        
        Args:
            file: FastAPI UploadFile object
            
        Raises:
            FileProcessingError: If file doesn't meet requirements
        """
        if not file.filename:
            raise FileProcessingError("No filename provided")
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise FileProcessingError(f"File type {file_extension} not allowed. Allowed types: {allowed}")

    @staticmethod
    async def process_uploaded_file(file: UploadFile) -> Tuple[str, str]:
        """
        Process uploaded file and extract text content.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (extracted_text, file_extension)
            
        Raises:
            FileProcessingError: If processing fails
        """
        try:
            file_extension = os.path.splitext(file.filename or "")[1].lower()
            
            file_content = await file.read()
            await file.seek(0)
            
            if file_extension == '.txt':
                return FileProcessor._extract_text_from_txt(file_content), file_extension
            elif file_extension == '.pdf':
                return await FileProcessor._extract_text_from_pdf(file_content), file_extension
            elif file_extension in ['.docx', '.doc']:
                return await FileProcessor._extract_text_from_docx(file_content), file_extension
            else:
                raise FileProcessingError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            raise FileProcessingError(f"Failed to process file: {str(e)}")

    @staticmethod
    def _extract_text_from_txt(content: bytes) -> str:
        """Extract text from TXT file."""
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('latin-1')
            except UnicodeDecodeError:
                return content.decode('utf-8', errors='ignore')

    @staticmethod
    async def _extract_text_from_pdf(content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            from pdfminer.high_level import extract_text
            from io import BytesIO
            
            def extract_sync():
                return extract_text(BytesIO(content))
            
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, extract_sync)
            
            if not text.strip():
                raise FileProcessingError("PDF appears to contain no extractable text")
                
            return text.strip()
            
        except ImportError:
            raise FileProcessingError("PDF processing not available - pdfminer.six not installed")
        except Exception as e:
            raise FileProcessingError(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    async def _extract_text_from_docx(content: bytes) -> str:
        """Extract text from DOCX/DOC file."""
        try:
            from docx import Document
            from io import BytesIO
            
            def extract_sync():
                doc = Document(BytesIO(content))
                paragraphs = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        paragraphs.append(paragraph.text.strip())
                return '\n\n'.join(paragraphs)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, extract_sync)
            
            if not text.strip():
                raise FileProcessingError("Document appears to contain no extractable text")
                
            return text.strip()
            
        except ImportError:
            raise FileProcessingError("DOCX processing not available - python-docx not installed")
        except Exception as e:
            raise FileProcessingError(f"Failed to extract text from document: {str(e)}")

    @staticmethod
    def get_document_type(filename: str) -> str:
        """
        Determine document type based on filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Document type string
        """
        filename_lower = filename.lower()
        
        if any(term in filename_lower for term in ['contract', 'agreement', 'terms']):
            return 'contract'
        elif any(term in filename_lower for term in ['lease', 'rental']):
            return 'lease'
        elif any(term in filename_lower for term in ['policy', 'insurance']):
            return 'policy'
        elif any(term in filename_lower for term in ['manual', 'guide', 'handbook']):
            return 'manual'
        elif any(term in filename_lower for term in ['legal', 'law', 'statute']):
            return 'legal'
        else:
            return 'document'

    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        Clean filename for use as document title.
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned title string
        """
        if not filename:
            return ""
        
        name_without_ext = os.path.splitext(filename)[0]
        cleaned = name_without_ext.replace('_', ' ').replace('-', ' ')
        
        # Title case
        return cleaned.title()