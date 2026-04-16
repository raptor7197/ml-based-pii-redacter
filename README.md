# Smart-Redact: PII Detection & Redaction System

Smart-Redact is an automated, multi-format file processing system designed to detect and securely redact Personally Identifiable Information (PII) from sensitive documents. It ensures that cybersecurity consultants can analyze documents safely without exposing client data.

## System Architecture

The application uses a decoupled client-server architecture with dedicated file processing pipelines:

+-------------------+       +-------------------+       +-----------------------+
|                   |       |                   |       |                       |
|  Streamlit UI     |<----->|  FastAPI Backend  |<----->|  AI/ML Pipeline       |
|  (File Upload,    | REST  |  (API Layer,      |       |  (spaCy, Presidio,    |
|   Preview,        | API   |   File Handlers)  |       |   Tesseract OCR)      |
|   Download)       |       |                   |       |                       |
+-------------------+       +---------+---------+       +-----------------------+
                                      |
                                      v
                            +---------+---------+
                            |                   |
                            | File Processors   |
                            | (PDF, Docx, Excel)|
                            |                   |
                            +-------------------+

## Key Features

- Multi-Format Processing: Support for PDFs, Microsoft Word (.docx), Excel (.xlsx), and Images.
- Intelligent PII Detection: Leverages Natural Language Processing (NLP) and regex patterns to identify names, emails, phone numbers, SSNs, credit cards, and more.
- True Redaction: PII is completely removed and replaced with block characters at the structural level, ensuring the data cannot be copied or recovered.
- Secure Previews: The frontend provides a side-by-side view with masked original text, guaranteeing zero PII exposure even during the review phase.

## Technology Stack

- Frontend: Python, Streamlit, Pandas
- Backend: Python, FastAPI, Uvicorn
- File Processing: PyPDF2, python-docx, openpyxl
- AI & NLP: spaCy, Microsoft Presidio

## Quick Start Guide

### 1. Start the Backend API

Open a terminal, navigate to the backend directory, activate the environment, and run the FastAPI server:

    cd backend
    source .venv/bin/activate
    python -m uvicorn app.api.main:app --reload

The backend will be available at http://127.0.0.1:8000.

### 2. Start the Frontend UI

Open a second terminal, navigate to the frontend directory, and run the Streamlit application:

    cd frontend
    # Ensure backend URL is passed if different from localhost
    BACKEND_URL=http://127.0.0.1:8000 streamlit run app.py

The frontend UI will automatically open in your default browser at http://localhost:8501.