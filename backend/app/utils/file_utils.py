"""
File utilities for handling uploads and validation
Handles files coming from React frontend uploads
"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
import aiofiles
from typing import Optional

from app.core.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, INPUT_DIR

async def save_uploaded_file(file: UploadFile) -> Path:
    """
    Save an uploaded file from React frontend to temporary storage
    
    Args:
        file: FastAPI UploadFile object from frontend
        
    Returns:
        Path to the saved file
        
    Raises:
        HTTPException: If file is invalid or save fails
    """
    # Generate unique filename to avoid conflicts
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix.lower()
    unique_filename = f"{file_id}{file_extension}"
    
    # Create full path
    file_path = INPUT_DIR / unique_filename
    
    # Ensure input directory exists
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Save file asynchronously (good for large files)
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)
        
        return file_path
    
    except Exception as e:
        # Clean up if save failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

def validate_file(file: UploadFile) -> bool:
    """
    Validate uploaded file from React frontend
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        True if file is valid, False otherwise
    """
    if not file.filename:
        return False
    
    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        return False
    
    return True

def cleanup_file(file_path: Path) -> None:
    """
    Clean up temporary file after processing
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        # Log error in production, but don't fail the request
        pass