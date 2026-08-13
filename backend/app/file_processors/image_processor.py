"""
Image Processor with OCR capability
Processes images uploaded from React frontend and extracts text using Tesseract OCR
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
from typing import Dict, Any

from .base_processor import BaseFileProcessor
from app.core.config import TESSERACT_CONFIG, IMAGE_PREPROCESSING, TESSERACT_CMD

class ImageProcessor(BaseFileProcessor):
    """
    Processes image files and extracts text using OCR
    Handles images uploaded from React frontend
    """
    
    def __init__(self, file_path: str | Path):
        super().__init__(file_path)
        
        # Configure pytesseract to use our Tesseract installation
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        
        # Validate that this is actually an image file
        if self.file_type != 'image':
            raise ValueError(f"ImageProcessor can only process images, got: {self.file_type}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        if not IMAGE_PREPROCESSING:
            return image
        
        # Convert palette or other modes to RGB first
        if image.mode in ('P', 'L', 'LA'):
            # For palette images, convert to RGBA first to preserve transparency, then to RGB
            if image.mode == 'P':
                image = image.convert('RGBA')
            image = image.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Scale up small images for better OCR (minimum 600px width)
        width, height = image.size
        if width < 600:
            scale_factor = 600 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    def extract_text(self) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Returns:
            Dict containing:
                - text: Extracted text content
                - confidence: OCR confidence score
                - metadata: Image metadata
                - preprocessing: Whether preprocessing was applied
        """
        try:
            # Open image
            image = Image.open(self.file_path)
            original_size = image.size
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text using Tesseract with multiple configurations
            extracted_text = ""
            best_confidence = 0
            best_score = 0  # Combined score considering both length and confidence
            
            # Try multiple OCR configurations
            ocr_configs = [
                '--oem 3 --psm 6',  # Default: Uniform block of text
                '--oem 3 --psm 3',  # Fully automatic page segmentation
                '--oem 3 --psm 8',  # Single word
                '--oem 3 --psm 7',  # Single text line
                '--oem 3 --psm 13', # Raw line
            ]
            
            for config in ocr_configs:
                try:
                    test_text = pytesseract.image_to_string(processed_image, config=config).strip()
                    
                    if test_text:  # If we found text
                        # Get confidence for this configuration
                        test_confidence_data = pytesseract.image_to_data(
                            processed_image, 
                            output_type=pytesseract.Output.DICT,
                            config=config
                        )
                        test_confidences = [int(conf) for conf in test_confidence_data['conf'] if int(conf) > 0]
                        test_avg_confidence = sum(test_confidences) / len(test_confidences) if test_confidences else 0
                        
                        # Calculate a combined score that considers both text length and confidence
                        # Prioritize longer text but still consider confidence
                        text_length_score = min(len(test_text) / 100, 10)  # Cap at 10x multiplier
                        combined_score = (test_avg_confidence * 0.3) + (text_length_score * 70)
                        
                        # Use the result with highest combined score
                        if combined_score > best_score:
                            extracted_text = test_text
                            best_confidence = test_avg_confidence
                            best_score = combined_score
                            confidence_data = test_confidence_data
                            
                except Exception as e:
                    continue
            
            # If no config worked, use the default config one more time and get its confidence data
            if not extracted_text:
                extracted_text = pytesseract.image_to_string(processed_image, config=TESSERACT_CONFIG).strip()
                confidence_data = pytesseract.image_to_data(
                    processed_image, 
                    output_type=pytesseract.Output.DICT,
                    config=TESSERACT_CONFIG
                )
                confidences = [int(conf) for conf in confidence_data['conf'] if int(conf) > 0]
                best_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Prepare metadata
            metadata = {
                'original_size': original_size,
                'file_size_bytes': self.file_path.stat().st_size,
                'words_detected': len([word for word in confidence_data['text'] if word.strip()]),
                'image_mode': image.mode
            }
            
            # If no text found, provide more helpful message
            if not extracted_text:
                extracted_text = "No text found in image"
            
            return {
                'text': extracted_text,
                'confidence': round(best_confidence, 2),
                'metadata': metadata,
                'preprocessing': IMAGE_PREPROCESSING
            }
            
        except Exception as e:
            return {
                'text': f'Error processing image: {str(e)}',
                'confidence': 0,
                'metadata': {'error': str(e)},
                'preprocessing': IMAGE_PREPROCESSING
            }