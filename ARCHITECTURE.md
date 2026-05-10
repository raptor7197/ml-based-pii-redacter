# Smart-Redact System Architecture

This document details the architectural design and object relationships of the Smart-Redact application using a UML Class and Component Diagram.

## System UML Diagram

The diagram below illustrates the separation of concerns between the Streamlit frontend, the FastAPI backend, the file processor strategy pattern, and the underlying NLP/AI core.

```mermaid
classDiagram
    %% Frontend Components
    class StreamlitFrontend {
        +tab_upload()
        +tab_preview()
        +tab_history()
        +tab_export()
        +upload_file_to_backend(file)
        +download_redacted_file(filename)
        +get_processed_files_history()
    }

    %% Backend API Layer
    class FastAPIServer {
        +POST /api/upload
        +GET /api/download/{filename}
        +GET /api/health
        +GET /api/history
    }

    %% Core Processors & Factory
    class ProcessorFactory {
        <<factory>>
        +get_processor(file_path) BaseFileProcessor
    }

    class BaseFileProcessor {
        <<abstract>>
        +file_path : str
        +file_type : str
        +pii_detector : PIIDetector
        +extract_text() Dict
        +process_file(file_path, output_dir) Dict
        +validate_file(file_path) bool
    }

    class PDFProcessor {
        +nlp : spacy.Language
        +process_file(file_path, output_dir)
        -_extract_text_with_layout(file_path)
        -_create_redacted_pdf(original, layout, pii, output)
    }

    class WordProcessor {
        +process_file(file_path, output_dir)
        -_extract_text_from_docx(file_path)
        -_create_redacted_docx(original, text, pii, output)
    }

    class ExcelProcessor {
        +pii_findings : List
        +extract_text() Dict
        +create_redacted_excel(original_filename) Path
    }

    class ImageProcessor {
        +extract_text() Dict
    }

    %% AI & Data Transformation Layer
    class PIIDetector {
        +analyzer : PresidioAnalyzer
        +detect_pii(text) List
        +detect_pii_with_layout(doc) Dict
    }

    class PIIMasker {
        <<utility>>
        +mask_pii_value(value, entity_type) str
        +mask_text_content(text) str
    }

    %% System Relationships
    StreamlitFrontend --> FastAPIServer : HTTP REST API
    FastAPIServer --> ProcessorFactory : Requests File Processor
    FastAPIServer --> PIIMasker : Secures UI Preview Payloads
    
    ProcessorFactory ..> PDFProcessor : Instantiates
    ProcessorFactory ..> WordProcessor : Instantiates
    ProcessorFactory ..> ExcelProcessor : Instantiates
    ProcessorFactory ..> ImageProcessor : Instantiates

    PDFProcessor --|> BaseFileProcessor : Extends
    WordProcessor --|> BaseFileProcessor : Extends
    ExcelProcessor --|> BaseFileProcessor : Extends
    ImageProcessor --|> BaseFileProcessor : Extends

    BaseFileProcessor --> PIIDetector : Uses for PII Analysis
```

## Component Overview

1. **Frontend (Streamlit)**: Acts as the visual presentation layer. It sends files, receives masked representations, and retrieves completed redacted files from the backend APIs.
2. **Backend (FastAPI)**: Coordinates the upload lifecycle, passes files to the `ProcessorFactory`, sanitizes text output via `PIIMasker` to prevent PII exposure in the UI payload, and manages the file download state.
3. **Processor Pipeline**: The `ProcessorFactory` pattern is used to instantiate the appropriate format-specific processor (`PDFProcessor`, `WordProcessor`, `ExcelProcessor`, etc.) inheriting from `BaseFileProcessor`.
4. **AI Core (PIIDetector)**: Handles regex matching, OCR, layout-aware entity detection, and Presidio-driven NLP tasks to determine coordinates and text spans containing sensitive data.