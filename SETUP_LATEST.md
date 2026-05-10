# Smart-Redact Setup Instructions - Latest Build

**Complete Document Processing & PII Redaction System**

## Prerequisites
- Docker Desktop installed and running
- Node.js 18+ installed
- Git installed

## Setup Steps

### 1. Clone Repository
```bash
git clone https://github.com/ArshSharan/Smart-Redact.git
cd Smart-Redact
```

### 2. Backend Setup
```bash
cd backend
docker build -t smart-redact-backend .
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

### 4. Run Application

#### Option A: Manual Start (Recommended)
```bash
# Terminal 1: Start Backend
cd backend
docker run --rm -p 8000:8000 -v ./data:/app/data --name SmartRedact_Testing smart-redact-backend

# Terminal 2: Start Frontend
cd ../frontend
npm run dev
```

#### Option B: Docker Desktop GUI
1. Open Docker Desktop
2. Go to Images > smart-redact-backend
3. Click "Run"
4. Set Host port to 8000
5. Add volume mount: `./data:/app/data`
6. Click "Run"
7. In separate terminal: `cd frontend; npm run dev`

### 5. Verify Setup
- Backend Health: http://localhost:8000/health
- Frontend: http://localhost:5173
- API Documentation: http://localhost:8000/docs

## Application Features

### Document Processing
- **Excel Processing**: Complete Excel (.xlsx, .xls) file processing with PII detection and redaction
- **PDF Processing**: Secure PDF document processing with true text removal (not just visual covering)
- **Word Document Processing**: Microsoft Word (.docx, .doc) processing with structure preservation
- **Image OCR**: Image text extraction for JPG, PNG, TIFF, BMP formats

### Security Features
- **True Redaction**: PII is completely removed from documents, not just visually hidden
- **Copy Protection**: Redacted content cannot be selected, copied, or recovered
- **Content Validation**: Final documents are verified to contain no original PII
- **Professional Formatting**: Redacted areas use block characters (█) for clear visual indication

### PII Detection
- **Email Addresses**: Complete email pattern detection
- **Phone Numbers**: US and international phone format recognition
- **Social Security Numbers**: SSN pattern matching
- **Credit Cards**: Major credit card number detection
- **IP Addresses**: IPv4 address identification
- **URLs**: Web address detection
- **Dates**: Various date format recognition
- **Names & Organizations**: NLP-based entity detection

### Download Features
- **Original Format Preservation**: Documents maintain their original structure and formatting
- **Clean Filenames**: Redacted files use format: `OriginalName_REDACTED_YYYYMMDD_HHMM.extension`
- **Instant Download**: Processed files available immediately after processing

## Project Structure
```
Smart-Redact/
├── .git/                            # Git repository data
├── .gitignore                       # Git ignore rules
├── .venv/                           # Python virtual environment
├── data/                            # Application data directory
├── backend/
│   ├── .dockerignore                # Docker ignore rules
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── main.py              # Main API endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Application configuration
│   │   │   └── pii_detector.py      # PII detection engine
│   │   ├── file_processors/
│   │   │   ├── __init__.py
│   │   │   ├── base_processor.py    # Base file processor class
│   │   │   ├── excel_processor.py   # Excel processing logic
│   │   │   ├── pdf_processor.py     # PDF document processing
│   │   │   ├── word_processor.py    # Word document processing
│   │   │   └── image_processor.py   # OCR image processing
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_utils.py        # File handling utilities
│   ├── data/                        # Backend data storage
│   ├── Dockerfile                   # Latest backend container
│   └── requirements.txt             # Python dependencies
├── frontend/
│   ├── .dockerignore                # Frontend Docker ignore
│   ├── .gitignore                   # Frontend Git ignore
│   ├── Dockerfile                   # Frontend container (production)
│   ├── eslint.config.js             # ESLint configuration
│   ├── index.html                   # Main HTML template
│   ├── nginx.conf                   # Nginx configuration
│   ├── package.json                 # Node dependencies
│   ├── package-lock.json            # Locked dependency versions
│   ├── public/                      # Static assets
│   ├── README.md                    # Frontend documentation
│   ├── src/
│   │   ├── App.jsx                  # Main React component
│   │   ├── App.css                  # UI styling
│   │   └── main.jsx                 # React entry point
│   └── vite.config.js               # Vite build configuration
├── EXCEL_IMPLEMENTATION.md          # Excel feature documentation
├── README.md                        # Main project documentation
└── SETUP_LATEST.md                  # Setup instructions (this file)
```

## Technical Notes
- **Backend**: Python 3.11 with FastAPI framework
- **Frontend**: React 18 + Vite for fast development and building
- **Document Processing**: 
  - Excel: openpyxl for reading/writing .xlsx files
  - PDF: pypdfium2 for text extraction, ReportLab for secure redaction
  - Word: python-docx for .docx processing
  - Images: Tesseract OCR for text extraction
- **PII Detection**: Advanced regex patterns + spaCy NLP + Presidio enterprise patterns
- **Security**: True text removal ensures no PII can be recovered from redacted documents
- **Containerization**: Docker for consistent deployment and dependency management
- **File Storage**: Persistent volume mounting for processed file downloads

## Security Features
- **Zero-Trust Redaction**: Original PII text is never included in final documents
- **Content Validation**: Automated verification that no PII remains in processed files
- **Copy Protection**: Redacted areas cannot be selected or copied from final documents
- **Professional Output**: Block character redaction (█) matching original text length

## Troubleshooting
- **Container name conflict**: If you get "container name already in use" error:
  - **PowerShell**: `docker stop smart-redact-backend; docker rm smart-redact-backend`
  - **Or use --rm flag**: `docker run --rm -p 8000:8000 -v ./data:/app/data smart-redact-backend` (auto-removes container when stopped)
- **Backend not responding**: Ensure Docker container is running with `docker ps`
- **Frontend connection errors**: Verify backend is accessible at http://localhost:8000/health
- **File upload failures**: Check Docker volume mounting for data persistence
- **Build failures**: Ensure Docker Desktop has sufficient memory allocated (4GB+)
- **npm issues**: Clear cache with `npm cache clean --force` and retry `npm install`

## File Structure
```
Smart-Redact/
├── backend/
│   ├── app/
│   │   ├── api/main.py              # FastAPI routes and file handling
│   │   ├── core/
│   │   │   ├── config.py            # Application configuration
│   │   │   └── pii_detector.py      # Multi-method PII detection engine
│   │   ├── file_processors/
│   │   │   ├── base_processor.py    # Abstract base processor
│   │   │   ├── excel_processor.py   # Excel file processing
│   │   │   ├── pdf_processor.py     # Secure PDF processing & redaction
│   │   │   ├── word_processor.py    # Word document processing
│   │   │   └── image_processor.py   # OCR image processing
│   │   └── utils/file_utils.py      # File handling utilities
│   ├── data/                        # File storage (mounted volume)
│   ├── Dockerfile                   # Container configuration
│   └── requirements.txt             # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main React application
│   │   ├── App.css                  # UI styling and themes
│   │   └── main.jsx                 # React entry point
│   ├── package.json                 # Node.js dependencies
│   └── vite.config.js               # Build configuration
├── data/                            # Persistent file storage
├── SETUP_LATEST.md                  # Setup instructions (this file)
├── PDF_DOCS_IMPLEMENTATION.md       # PDF/Word processing documentation
└── README.md                        # Project overview
```