"""
Base File Processor
Abstract class that defines the interface for all file processors
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import mimetypes

class BaseFileProcessor(ABC):
    """
    Abstract base class for all file processors
    Defines the common interface for text extraction from different file types
    """
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.file_type = self._detect_file_type()
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
    
    def _detect_file_type(self) -> str:
        """Detect file type based on extension and MIME type"""
        extension = self.file_path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(self.file_path))
        
        return {
            '.pdf': 'pdf',
            '.xlsx': 'excel', 
            '.xls': 'excel',
            '.pptx': 'powerpoint',
            '.ppt': 'powerpoint',
            '.jpg': 'image',
            '.jpeg': 'image', 
            '.png': 'image',
            '.tiff': 'image',
            '.bmp': 'image',
            '.txt': 'text',
            '.csv': 'csv'
        }.get(extension, 'unknown')
    
    @abstractmethod
    def extract_text(self) -> Dict[str, Any]:
        """
        Extract text content from the file
        
        Returns:
            Dict containing:
                - text: str - Extracted text content
                - metadata: dict - File metadata (pages, size, etc.)
                - confidence: float - Extraction confidence (for OCR)
        """
        pass
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get basic file information"""
        stat = self.file_path.stat()
        return {
            'filename': self.file_path.name,
            'file_type': self.file_type,
            'size_bytes': stat.st_size,
            'extension': self.file_path.suffix.lower()
        }

class ProcessorFactory:
    """Factory class to create appropriate processor for file type"""
    
    @staticmethod
    def get_processor(file_path: str | Path) -> BaseFileProcessor:
        """
        Create and return appropriate processor for the given file
        
        Args:
            file_path: Path to the file to process
        Returns:
            Appropriate processor instance
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            # Try to use real OCR first, fall back to mock if Tesseract not available
            try:
                import pytesseract
                from app.core.config import TESSERACT_CMD
                
                # Configure Tesseract path before testing
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
                
                # Test if Tesseract is available
                pytesseract.get_tesseract_version()
                
                from .image_processor import ImageProcessor
                return ImageProcessor(file_path)
            except (pytesseract.TesseractNotFoundError, FileNotFoundError, Exception):
                # Tesseract not available, use mock processor
                from .mock_image_processor import MockImageProcessor
                return MockImageProcessor(file_path)
                
        elif extension in ['.xlsx', '.xls']:
            from .excel_processor import ExcelProcessor
            return ExcelProcessor(file_path)
            
        elif extension == '.pdf':
            from .pdf_processor import PDFProcessor
            return PDFProcessor(file_path)
            
        elif extension in ['.docx', '.doc']:
            from .word_processor import WordProcessor
            return WordProcessor(file_path)
            
        else:
            raise NotImplementedError(f"Processor for {extension} not yet implemented")