import io
import PyPDF2
from docx import Document as DocxDocument
from typing import Tuple, Optional
from fastapi import UploadFile
from pathlib import Path
from core.config import settings

class FileProcessor:
    """Handle file processing for different document types."""
    
    ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS
    MAX_FILE_SIZE = settings.MAX_FILE_SIZE
    
    @classmethod
    async def process_uploaded_file(cls, file: UploadFile) -> Tuple[str, str]:
        """Process uploaded file and extract text content."""
        
        # Validate file size
        if file.size and file.size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {cls.MAX_FILE_SIZE // (1024*1024)}MB limit")
        
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower() if file.filename else ""
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type. Allowed types: {', '.join(cls.ALLOWED_EXTENSIONS)}")
        
        # Read file content
        content = await file.read()
        
        # Reset file pointer for potential re-reading
        await file.seek(0)
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text_content = cls._extract_pdf_text(content)
        elif file_extension in ['.docx', '.doc']:
            text_content = cls._extract_docx_text(content)
        elif file_extension == '.txt':
            text_content = content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return text_content, file_extension
    
    @classmethod
    def process_local_file(cls, file_path: Path) -> Tuple[str, str]:
        """Process a local file and extract text content."""
        
        if not file_path.exists():
            raise ValueError("File does not exist")
        
        # Validate file size
        file_size = file_path.stat().st_size
        if file_size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {cls.MAX_FILE_SIZE // (1024*1024)}MB limit")
        
        # Validate file extension
        file_extension = file_path.suffix.lower()
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type. Allowed types: {', '.join(cls.ALLOWED_EXTENSIONS)}")
        
        # Read and process file
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text_content = cls._extract_pdf_text(content)
        elif file_extension in ['.docx', '.doc']:
            text_content = cls._extract_docx_text(content)
        elif file_extension == '.txt':
            text_content = content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return text_content, file_extension
    
    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                raise ValueError("Could not extract text from PDF. The document might be image-based.")
            
            return text.strip()
        
        except Exception as e:
            raise ValueError(f"Error processing PDF file: {str(e)}")
    
    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            import tempfile
            import os
            
            # Create a temporary file to work with python-docx
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                
                # Extract text using python-docx
                doc = DocxDocument(tmp_file.name)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                if not text.strip():
                    raise ValueError("Could not extract text from document. The document might be empty.")
                
                return text.strip()
        
        except Exception as e:
            raise ValueError(f"Error processing DOCX file: {str(e)}")
    
    @staticmethod
    def get_document_type(filename: str) -> str:
        """Determine document type from filename."""
        filename_lower = filename.lower()
        
        # Legal document keywords
        legal_keywords = [
            'contract', 'agreement', 'lease', 'terms', 'conditions',
            'legal', 'law', 'court', 'settlement', 'nda', 'privacy',
            'policy', 'license', 'will', 'testament', 'deed', 'patent',
            'copyright', 'trademark', 'employment', 'divorce', 'custody'
        ]
        
        for keyword in legal_keywords:
            if keyword in filename_lower:
                return 'legal'
        
        # Default to legal for now
        return 'legal'
