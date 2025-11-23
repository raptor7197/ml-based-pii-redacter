# An AI-Powered Cybersecurity File Cleansing & Analysis System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Problem Statement

Cybersecurity consultants face a critical challenge when analyzing sensitive client documents:

**The Challenge**: Consultants receive mixed file formats (Excel, PDFs, images, PowerPoint, text) containing sensitive client data including logos, company names, and personally identifiable information (PII). They need to:
- Extract meaningful cybersecurity insights from these documents
- Completely anonymize all client-identifying information
- Standardize the analysis process across different file formats
- Generate actionable reports without compromising client privacy

**Current Pain Points**:
- Manual redaction is time-consuming and error-prone
- No standardized process for multi-format document analysis
- Risk of accidental data exposure during analysis
- Difficulty extracting structured insights from unstructured documents

## Our Solution Approach

Smart-Redact automates the entire pipeline from sensitive document intake to anonymized insight generation:

### Core Processing Pipeline
```
File Upload → PII Detection & Removal → Content Extraction → Security Analysis → Standardized Reports
```

### Key Solution Components

**1. Multi-Format File Processing**
- Handle Excel spreadsheets, PDF documents, PowerPoint presentations, images, and text files
- Extract text content while preserving structure and context
- OCR integration for scanned documents and image-based content

**2. Intelligent PII Detection & Redaction**
- AI-powered identification of company names, logos, personal information
- Context-aware masking that preserves document structure
- Pattern-based detection for emails, phone numbers, addresses, etc.

**3. Cybersecurity Content Analysis**
- Automated extraction of IAM policy statements
- Firewall rule identification and parsing
- IDS/IPS log analysis and categorization
- Security configuration assessment

**4. Insight Generation**
- Transform raw extracted data into actionable cybersecurity insights
- Generate standardized reports using consultant templates
- Highlight security gaps, misconfigurations, and recommendations

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend │    │   AI/ML Pipeline│
│   File Upload   │◄──►│   API Layer      │◄──►│   Processing    │
│   Results View  │    │   File Handlers  │    │   Analysis      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Technology Stack Decision

### Backend: Python + FastAPI

**Why Python?**
- **Rich AI/ML Ecosystem**: Extensive libraries for NLP (spaCy), computer vision (OpenCV), and machine learning (Transformers)
- **File Processing Libraries**: Mature tools for handling all target file formats (PyPDF2, openpyxl, python-pptx)
- **OCR Integration**: Seamless integration with Tesseract and cloud OCR services
- **Security Libraries**: Robust PII detection tools like Microsoft's Presidio

**Why FastAPI?**
- **High Performance**: Async support for concurrent file processing
- **Auto Documentation**: Built-in API documentation for team collaboration
- **Type Safety**: Python type hints improve code reliability
- **Easy Integration**: Simple REST API interface for frontend communication

### Frontend: React.js

**Why React?**
- **Component-Based Architecture**: Modular UI components for file upload, processing status, and results display
- **Rich Ecosystem**: Extensive libraries for file handling (react-dropzone) and UI components
- **Team Familiarity**: Leverages existing frontend development skills
- **Real-time Updates**: Easy integration with backend for processing status updates

### Key Libraries & Tools

**AI/ML Processing**:
- `spaCy` - Named Entity Recognition for identifying people, organizations
- `presidio-analyzer` - Microsoft's enterprise-grade PII detection
- `transformers` - Hugging Face models for advanced text analysis
- `pytesseract` - OCR for extracting text from images and scanned documents

**File Processing**:
- `PyPDF2/pdfplumber` - Comprehensive PDF text and table extraction
- `openpyxl` - Excel file processing with formula and formatting support
- `python-pptx` - PowerPoint slide content extraction
- `Pillow (PIL)` - Image processing and manipulation

## Development Phases

### Phase 1: Core File Processing (Foundation)
- Build individual processors for each file format
- Implement basic text extraction pipeline
- Set up React frontend with file upload capability

### Phase 2: PII Detection & Redaction (Security)
- Integrate spaCy and Presidio for comprehensive PII detection
- Develop intelligent masking algorithms
- Add logo detection using computer vision techniques

### Phase 3: Security Content Analysis (Intelligence)
- Build parsers for cybersecurity-specific content patterns
- Implement AI-powered insight generation
- Create standardized report templates

### Phase 4: Integration & Optimization (Polish)
- Frontend-backend integration and testing
- Performance optimization for large file processing
- User interface refinement and error handling

## Success Metrics

- **Processing Speed**: Target 2-5 seconds per document page
- **PII Detection Accuracy**: 98%+ with combined AI models
- **Format Support**: 100% coverage for target file types (PDF, Excel, PPT, Images, Text)
- **User Experience**: Single-click processing with real-time status updates

---

*Smart-Redact: Making sensitive data analysis safe, efficient, and intelligent.*
