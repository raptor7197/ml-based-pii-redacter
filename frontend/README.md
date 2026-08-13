# Smart-Redact Streamlit Frontend

A user-friendly Streamlit interface for the PII detection and redaction backend API.

## Features

- 📤 **File Upload**: Drag-and-drop or browse to upload files
- 🔍 **PII Detection**: Automatically detects and redacts PII in uploaded files
- 📊 **Visualization**: View detailed PII detection summaries and statistics
- 📥 **Download**: Download redacted files directly from the interface
- ⚙️ **Status Monitoring**: Real-time backend health checking

## Supported File Types

- **Documents**: PDF, Word (.docx, .doc)
- **Spreadsheets**: Excel (.xlsx, .xls)
- **Images**: JPG, PNG, TIFF, BMP

## PII Types Detected

- Email Addresses
- Phone Numbers
- Social Security Numbers (SSN)
- Credit Card Numbers
- IP Addresses
- URLs
- Dates of Birth
- Passport Numbers
- License Plates

## Quick Start

### Prerequisites

1. **Backend must be running**: The Streamlit app requires the FastAPI backend to be running on port 8000.

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Running the App

```bash
# Start the Streamlit app
streamlit run app.py
```

The app will be available at `http://localhost:8501` by default.

### Custom Backend URL

If your backend is running on a different URL or port:

```bash
# Using environment variable
BACKEND_URL=http://your-backend-url:port streamlit run app.py

# Example
BACKEND_URL=http://192.168.1.100:8000 streamlit run app.py
```

## Using Docker

```bash
# Build the image
docker build -t smart-redact-frontend .

# Run the container
docker run -p 8501:8501 -e BACKEND_URL=http://backend:8000 smart-redact-frontend
```

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Streamlit     │  HTTP   │   FastAPI       │
│   Frontend      │ ──────> │   Backend       │
│   (Port 8501)   │         │   (Port 8000)   │
└─────────────────┘         └─────────────────┘
                                  │
                                  ▼
                          ┌─────────────────┐
                          │  File Storage   │
                          │  & Processing   │
                          └─────────────────┘
```

## Project Structure

```
frontend/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── Dockerfile         # Docker configuration
```

## Troubleshooting

### Backend Not Connected

If you see "Backend Not Connected" error:
1. Ensure the backend is running: `cd backend && uvicorn app.api.main:app --reload`
2. Check that the backend is accessible at `http://localhost:8000`
3. Verify no firewall is blocking the connection

### File Upload Fails

- Check file size (max 100MB)
- Ensure file type is supported
- Verify backend has write permissions to data directories

### Processing Timeout

- Large files may take longer to process
- Increase timeout in `app.py` if needed
- Check backend logs for processing status
