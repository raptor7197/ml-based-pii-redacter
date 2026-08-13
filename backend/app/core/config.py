"""
Application configuration settings
"""
import os
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input_files"
OUTPUT_DIR = DATA_DIR / "processed_files"

# File upload settings
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.docx', '.xlsx', '.pptx', 
    '.jpg', '.jpeg', '.png', '.tiff', '.bmp',
    '.txt', '.csv'
}

# OCR settings
TESSERACT_CONFIG = '--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6

# Auto-detect Tesseract installation
def get_tesseract_cmd():
    """Auto-detect Tesseract installation across different environments"""
    # Check if running in Docker (Tesseract installed via apt)
    docker_path = '/usr/bin/tesseract'
    if os.path.exists(docker_path):
        return docker_path
    
    # Check system PATH
    system_tesseract = shutil.which('tesseract')
    if system_tesseract:
        return system_tesseract
    
    # Common Windows installations
    windows_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    
    for path in windows_paths:
        if os.path.exists(path):
            return path
    
    # Default fallback - will work if tesseract is in PATH
    return 'tesseract'

TESSERACT_CMD = get_tesseract_cmd()
IMAGE_PREPROCESSING = True
DPI_THRESHOLD = 300  # Minimum DPI for good OCR results

# Processing settings
CHUNK_SIZE = 8192  # For file reading
CONCURRENT_PROCESSING = True
MAX_WORKERS = 4

# Security settings
DELETE_FILES_AFTER_PROCESSING = True
RETENTION_HOURS = 24

# Environment variables
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", 8000))