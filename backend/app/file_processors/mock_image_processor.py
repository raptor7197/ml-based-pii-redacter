from pathlib import Path
from typing import Dict, Any
import logging

from .base_processor import BaseFileProcessor

logger = logging.getLogger(__name__)

class MockImageProcessor(BaseFileProcessor):
    """
    Mock image processor for when Tesseract OCR is not available.
    Returns placeholder results to maintain API compatibility.
    """

    def __init__(self, file_path: str | Path):
        super().__init__(file_path)
        self.logger = logging.getLogger(__name__)

    def extract_text(self) -> Dict[str, Any]:
        """
        Mock text extraction that returns placeholder results.

        Returns:
            Dict containing mock extraction results
        """
        try:
            file_info = self.get_file_info()

            return {
                'text': '[OCR not available - Tesseract not installed]',
                'metadata': {
                    'filename': file_info['filename'],
                    'file_type': file_info['file_type'],
                    'size_bytes': file_info['size_bytes'],
                    'ocr_available': False,
                    'mock_processor': True
                },
                'confidence': 0.0,
                'pii_findings': [],
                'total_pii_count': 0,
                'entity_types': {}
            }

        except Exception as e:
            self.logger.error(f"Error in mock image processor: {str(e)}")
            return {
                'text': '',
                'metadata': {'error': str(e), 'mock_processor': True},
                'confidence': 0.0,
                'pii_findings': [],
                'total_pii_count': 0,
                'entity_types': {}
            }