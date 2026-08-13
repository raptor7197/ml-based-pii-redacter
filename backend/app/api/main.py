"""
Smart-Redact FastAPI Application
Simple API for handling file uploads from React frontend
"""

import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import DELETE_FILES_AFTER_PROCESSING
from app.core.pii_masker import mask_pii_value, mask_text_content
from app.file_processors.base_processor import ProcessorFactory
from app.utils.file_utils import cleanup_file, save_uploaded_file, validate_file

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Smart-Redact API",
    description="File upload and OCR processing for cybersecurity documents",
    version="1.0.0",
)

# Enable CORS so React can talk to our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend",
    ],  # React dev server + Docker
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Simple health check - shows API is running"""
    return {
        "message": "Smart-Redact API is running!",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "smart-redact-api"}


@app.post("/api/upload")
async def upload_and_process_file(file: UploadFile = File(...)):
    """
    Main endpoint: Upload file from React and process it

    This is what React will call when user uploads a file
    """
    try:
        # Step 1: Validate the uploaded file
        if not validate_file(file):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file. Allowed types: .jpg, .jpeg, .png, .tiff, .bmp, .xlsx, .xls, .pdf, .docx, .doc (max 100MB)",
            )

        # Step 2: Save uploaded file temporarily
        file_path = await save_uploaded_file(file)

        # Step 3: Get appropriate processor and process file
        processor = ProcessorFactory.get_processor(file_path)

        # Handle different processor interfaces
        if hasattr(processor, "process_file") and callable(processor.process_file):
            # New processors (PDF, Word) use process_file method
            extracted_data = processor.process_file(
                str(file_path), "data/processed_files"
            )
        else:
            # Legacy processors (Excel, Image) use extract_text method
            extracted_data = processor.extract_text()

        # Step 4: Prepare response based on file type and processor output
        file_extension = Path(file.filename).suffix.lower()

        if file_extension in [".pdf", ".docx", ".doc"]:
            # Handle PDF and Word document responses
            raw_text = extracted_data.get("masked_text", "")
            masked_text = mask_text_content(raw_text) if raw_text else ""

            # Mask PII findings
            raw_findings = extracted_data.get("pii_findings", [])
            masked_findings = []
            for finding in raw_findings:
                masked_finding = finding.copy()
                if "text" in masked_finding:
                    pii_type = masked_finding.get("entity_type", "UNKNOWN")
                    masked_finding["text"] = mask_pii_value(
                        str(masked_finding["text"]), pii_type
                    )
                if "original_value" in masked_finding:
                    pii_type = masked_finding.get("entity_type", "UNKNOWN")
                    masked_finding["original_value"] = mask_pii_value(
                        str(masked_finding["original_value"]), pii_type
                    )
                masked_findings.append(masked_finding)

            response_data = {
                "status": "success",
                "filename": file.filename,
                "file_type": file_extension[1:],  # Remove the dot
                "processing_status": extracted_data.get(
                    "processing_status", "completed"
                ),
                "total_entities": extracted_data.get("total_entities", 0),
                "entity_types": extracted_data.get("entity_types", {}),
                "confidence": extracted_data.get("confidence_score", 0),
                "pages_processed": extracted_data.get("pages_processed", 0),
                "layout_spans_processed": extracted_data.get(
                    "layout_spans_processed", 0
                ),
                "pii_findings": masked_findings,
                "masked_text": masked_text,
                "message": f"Successfully processed {file.filename}",
            }

            # Add download link if redacted file was created
            if extracted_data.get("redacted_file_path"):
                redacted_path = Path(extracted_data["redacted_file_path"])
                redacted_filename = redacted_path.name
                response_data["redacted_file_url"] = (
                    f"/api/download/{redacted_filename}"
                )
                response_data["redacted_filename"] = redacted_filename

        else:
            # Handle Excel and Image responses (legacy format)
            # NEVER send raw extracted text - mask it for safety
            raw_text = extracted_data.get("text", "")
            masked_text = mask_text_content(raw_text) if raw_text else ""

            response_data = {
                "status": "success",
                "filename": file.filename,
                "file_type": processor.file_type,
                "masked_text": masked_text,  # Only send masked text, never raw
                "confidence": extracted_data.get("confidence", 0),
                "metadata": extracted_data.get("metadata", {}),
                "message": f"Successfully processed {file.filename}",
            }

        # Add Excel-specific data if available
        if hasattr(processor, "pii_findings") and processor.pii_findings:
            # Mask all PII findings before sending to frontend
            masked_findings = []
            for finding in extracted_data.get("pii_findings", []):
                masked_finding = finding.copy()
                if "original_value" in masked_finding:
                    pii_type = masked_finding.get("entity_type", "UNKNOWN")
                    masked_finding["original_value"] = mask_pii_value(
                        str(masked_finding["original_value"]), pii_type
                    )
                masked_findings.append(masked_finding)

            response_data.update(
                {
                    "pii_findings": masked_findings,
                    "pii_summary": extracted_data.get("pii_summary", {}),
                    "total_pii_count": extracted_data.get("total_pii_count", 0),
                    "entity_types": extracted_data.get(
                        "pii_summary", {}
                    ),  # Use pii_summary as entity_types
                    "worksheets": extracted_data.get("worksheets", []),
                }
            )

            # Generate redacted Excel file if PII was found
            if (
                extracted_data.get("total_pii_count", 0) > 0
                and processor.file_type == "excel"
            ):
                try:
                    # Pass original filename for better naming
                    redacted_file_path = processor.create_redacted_excel(
                        original_filename=file.filename
                    )
                    # Create download URL for the redacted file
                    redacted_filename = redacted_file_path.name
                    response_data["redacted_file_url"] = (
                        f"/api/download/{redacted_filename}"
                    )
                    response_data["redacted_filename"] = redacted_filename
                except Exception as e:
                    logger.warning(f"Failed to create redacted Excel file: {str(e)}")

        # Step 5: Clean up temporary file (but keep redacted file for download)
        if DELETE_FILES_AFTER_PROCESSING:
            cleanup_file(file_path)

        return JSONResponse(response_data)

    except Exception as e:
        # If anything goes wrong, tell React what happened
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/download/{filename}")
async def download_redacted_file(filename: str):
    """
    Download endpoint for redacted files (Excel, PDF, Word)
    """
    try:
        # Security: Only allow downloads from the data directory
        file_path = Path("data/processed_files") / filename

        # Ensure the file exists and is within our allowed directory
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        # Additional security check to prevent directory traversal
        if not str(file_path.resolve()).startswith(
            str(Path("data/processed_files").resolve())
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        # Determine media type based on file extension
        file_extension = file_path.suffix.lower()
        media_types = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
        }

        media_type = media_types.get(file_extension, "application/octet-stream")

        # Return the file for download
        return FileResponse(
            path=str(file_path), filename=filename, media_type=media_type
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.get("/api/health")
async def detailed_health_check():
    """Check if all services are working"""
    return {
        "api": "running",
        "ocr": "available",
        "file_upload": "ready",
        "supported_formats": [
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".bmp",
            ".xlsx",
            ".xls",
            ".pdf",
            ".docx",
            ".doc",
        ],
        "pii_detection": "enabled",
    }


@app.get("/api/history")
async def get_processed_files_history():
    """
    Get list of all processed/redacted files in the output directory
    Returns file metadata and download links
    """
    try:
        processed_dir = Path("data/processed_files")

        if not processed_dir.exists():
            return JSONResponse({"files": []})

        files = []
        for file_path in sorted(
            processed_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            if file_path.is_file() and not file_path.name.startswith("."):
                stat = file_path.stat()
                files.append(
                    {
                        "filename": file_path.name,
                        "size_bytes": stat.st_size,
                        "size_human": _format_file_size(stat.st_size),
                        "modified": stat.st_mtime,
                        "modified_human": _format_timestamp(stat.st_mtime),
                        "download_url": f"/api/download/{file_path.name}",
                        "file_type": file_path.suffix.lower(),
                    }
                )

        return JSONResponse({"files": files, "total": len(files)})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def _format_timestamp(timestamp: float) -> str:
    """Format timestamp to readable string"""
    from datetime import datetime

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# For testing: run with python -m uvicorn app.api.main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000, reload=True)
