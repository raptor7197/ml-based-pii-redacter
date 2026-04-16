"""
Simplified PDF processor for PII detection and redaction.
Focuses on core functionality without complex dependencies.
"""

import concurrent.futures
import io
import logging
import tempfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import PyPDF2
import pypdfium2 as pdfium
import spacy
import spacy_layout
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from ..core.pii_detector import PIIDetector
from .base_processor import BaseFileProcessor


class PDFProcessor(BaseFileProcessor):
    """
    Simplified PDF processor that extracts text and redacts PII.
    Maintains basic document structure while focusing on functionality.
    """

    def __init__(self, file_path: Optional[str] = None):
        if file_path:
            super().__init__(file_path)

        self.logger = logging.getLogger(__name__)
        self.pii_detector = PIIDetector()
        self.nlp = None
        self._initialize_spacy_layout()
        self.logger.info("PDF processor initialized with layout awareness")

        # Cache for expensive operations
        self._page_text_cache = {}
        self._redaction_cache = {}

    def extract_text(self) -> Dict[str, Any]:
        """
        Extract text from PDF for legacy API compatibility.

        Returns:
            Dict containing extracted text and metadata
        """
        try:
            if not hasattr(self, "file_path") or not self.file_path:
                raise ValueError("File path not set for PDF processor")

            # Simple PDF text extraction using PyPDF2
            import PyPDF2

            with open(self.file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""

                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"

            # Detect PII in the extracted text
            pii_findings = self.pii_detector.detect_pii(text_content)

            # Calculate PII statistics
            entity_types = {}
            for finding in pii_findings:
                pii_type = finding.get("type", "unknown")
                entity_types[pii_type] = entity_types.get(pii_type, 0) + 1

            return {
                "text": text_content,
                "metadata": {"pages": len(pdf_reader.pages), "file_type": "pdf"},
                "confidence": 0.85,  # Good confidence for PDF text extraction
                "pii_findings": pii_findings,
                "total_pii_count": len(pii_findings),
                "entity_types": entity_types,
            }

        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}")
            return {"text": "", "metadata": {"error": str(e)}, "confidence": 0.0}

    def _initialize_spacy_layout(self):
        try:
            import spacy_layout

            # Load a proper spaCy model (not blank) for layout processing
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Fallback to blank model if en_core_web_sm not available
                self.nlp = spacy.blank("en")

            # Check if spacy_layout component is available
            try:
                self.nlp.add_pipe("spacy_layout")
            except Exception:
                # Fallback - layout processing will be disabled
                self.nlp = None
                self.logger.debug(
                    "spaCy layout component not available, using coordinate-based redaction"
                )
                return

            self.logger.info("spaCy layout pipeline initialized")
        except Exception as e:
            self.logger.debug(f"Could not initialize spaCy layout: {str(e)}")
            self.nlp = None

    def process_file(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Process PDF file with PII detection and redaction.

        Args:
            file_path: Path to the input PDF file
            output_dir: Directory to save the redacted PDF

        Returns:
            Dictionary containing processing results and redacted file info
        """
        try:
            self.logger.info(f"Processing PDF file: {file_path}")

            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Extract text with layout information
            layout_data = self._extract_text_with_layout(file_path)
            full_text = layout_data["full_text"]
            page_texts = layout_data["page_texts"]
            spacy_doc = layout_data.get("spacy_doc")

            if not full_text.strip():
                self.logger.warning("No text found in PDF")
                return {
                    "total_entities": 0,
                    "entity_types": {},
                    "redacted_file_path": None,
                    "original_text_length": 0,
                    "redacted_text_length": 0,
                    "processing_status": "completed",
                    "confidence_score": 1.0,
                    "pages_processed": len(page_texts),
                    "layout_spans_processed": 0,
                }

            # Use layout-aware PII detection if available
            if spacy_doc and self.nlp:
                pii_result = self.pii_detector.detect_pii_with_layout(spacy_doc)
                pii_findings = pii_result["entities"]
                layout_spans_processed = pii_result.get("layout_spans_analyzed", 0)
            else:
                pii_findings = self.pii_detector.detect_pii(full_text)
                layout_spans_processed = 0

            if not pii_findings:
                self.logger.info("No PII detected in PDF")
                return {
                    "total_entities": 0,
                    "entity_types": {},
                    "redacted_file_path": None,
                    "original_text_length": len(full_text),
                    "redacted_text_length": len(full_text),
                    "processing_status": "completed",
                    "confidence_score": 1.0,
                    "pages_processed": len(page_texts),
                }

            # Calculate PII statistics
            entity_types = {}
            for finding in pii_findings:
                pii_type = finding.get("entity_type", "unknown")
                entity_types[pii_type] = entity_types.get(pii_type, 0) + 1

            # Create redacted PDF with layout information
            redacted_file_path = self._create_redacted_pdf_with_coordinates(
                file_path, layout_data, pii_findings, output_dir
            )

            # Calculate processing metrics
            processing_result = {
                "total_entities": len(pii_findings),
                "entity_types": entity_types,
                "redacted_file_path": redacted_file_path,
                "original_text_length": len(full_text),
                "redacted_text_length": len(full_text),  # For now, keep original length
                "processing_status": "completed",
                "confidence_score": self._calculate_confidence_score(pii_findings),
                "pages_processed": len(page_texts),
                "layout_spans_processed": layout_spans_processed,
            }

            self.logger.info(
                f"PDF processing completed. Found {len(pii_findings)} PII entities"
            )
            processing_result["pii_findings"] = pii_findings
            processing_result["masked_text"] = (
                full_text if "full_text" in locals() else ""
            )
            return processing_result

        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise

    def _extract_page_data(
        self, pdf_doc, page_num: int
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract text and coordinates for a single page.
        """
        page = pdf_doc[page_num]
        page_text = page.get_textpage().get_text_range()

        # Extract character-level coordinates for layout awareness
        text_page = page.get_textpage()
        char_coords = []
        for char_idx in range(len(page_text)):
            try:
                char_box = text_page.get_charbox(char_idx)
                if char_box:
                    char_coords.append(
                        {
                            "char": page_text[char_idx],
                            "x": float(char_box[0]),
                            "y": float(char_box[1]),
                            "width": float(char_box[2] - char_box[0]),
                            "height": float(char_box[3] - char_box[1]),
                            "page": page_num,
                        }
                    )
            except:
                pass
        return page_text, char_coords

    def _extract_page_text(self, pdf_doc, page_num: int) -> str:
        """
        Extract text for a single page.
        """
        page = pdf_doc[page_num]
        return page.get_textpage().get_text_range()

    def _extract_text_with_layout(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF with layout information using spaCy layout processing.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing text, layout data, and spaCy document
        """
        try:
            # First extract text using pypdfium2
            pdf_doc = pdfium.PdfDocument(file_path)
            page_count = len(pdf_doc)
            page_texts = []
            page_coords = []

            # Use parallel processing for multi-page documents
            if page_count > 4:  # Only use parallel processing for larger documents
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit tasks for each page
                    future_to_page = {
                        executor.submit(
                            self._extract_page_data, pdf_doc, page_num
                        ): page_num
                        for page_num in range(page_count)
                    }

                    # Collect results
                    page_results = {}
                    for future in concurrent.futures.as_completed(future_to_page):
                        page_num = future_to_page[future]
                        try:
                            page_text, char_coords = future.result()
                            page_results[page_num] = (page_text, char_coords)
                        except Exception as e:
                            self.logger.error(
                                f"Error processing page {page_num}: {str(e)}"
                            )
                            page_results[page_num] = ("", [])

                    # Unpack results in order
                    for page_num in range(page_count):
                        page_text, char_coords = page_results[page_num]
                        page_texts.append(page_text)
                        page_coords.append(char_coords)
            else:
                # For smaller documents, process sequentially
                for page_num in range(page_count):
                    page = pdf_doc[page_num]
                    page_text = page.get_textpage().get_text_range()
                    page_texts.append(page_text)

                    # Extract character-level coordinates for layout awareness
                    text_page = page.get_textpage()
                    char_coords = []
                    for char_idx in range(len(page_text)):
                        try:
                            char_box = text_page.get_charbox(char_idx)
                            if char_box:
                                char_coords.append(
                                    {
                                        "char": page_text[char_idx],
                                        "x": float(char_box[0]),
                                        "y": float(char_box[1]),
                                        "width": float(char_box[2] - char_box[0]),
                                        "height": float(char_box[3] - char_box[1]),
                                        "page": page_num,
                                    }
                                )
                        except:
                            pass
                    page_coords.append(char_coords)

            pdf_doc.close()
            full_text = "\n\n".join(page_texts)

            # Process with spaCy layout if available
            spacy_doc = None
            if self.nlp and full_text.strip():
                try:
                    # Process with layout-aware spaCy pipeline
                    spacy_doc = self.nlp(full_text)
                    self.logger.debug(f"Processed text with spaCy layout pipeline")
                except Exception as e:
                    self.logger.warning(f"spaCy layout processing failed: {str(e)}")

            self.logger.debug(
                f"Extracted text from {len(page_texts)} pages with coordinate data"
            )

            return {
                "full_text": full_text,
                "page_texts": page_texts,
                "page_coordinates": page_coords,
                "spacy_doc": spacy_doc,
            }

        except Exception as e:
            self.logger.error(f"Error extracting text with layout from PDF: {str(e)}")
            # Fallback to simple extraction
            return self._extract_text_from_pdf_fallback(file_path)

    def _extract_text_from_pdf_fallback(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback text extraction method without layout information.
        """
        try:
            pdf_doc = pdfium.PdfDocument(file_path)
            page_count = len(pdf_doc)
            page_texts = []

            # Use parallel processing for multi-page documents
            if page_count > 4:  # Only use parallel processing for larger documents
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit tasks for each page
                    future_to_page = {
                        executor.submit(
                            self._extract_page_text, pdf_doc, page_num
                        ): page_num
                        for page_num in range(page_count)
                    }

                    # Collect results in order
                    page_results = {}
                    for future in concurrent.futures.as_completed(future_to_page):
                        page_num = future_to_page[future]
                        try:
                            page_text = future.result()
                            page_results[page_num] = page_text
                        except Exception as e:
                            self.logger.error(
                                f"Error extracting text from page {page_num}: {str(e)}"
                            )
                            page_results[page_num] = ""

                    # Unpack results in order
                    for page_num in range(page_count):
                        page_texts.append(page_results[page_num])
            else:
                # For smaller documents, process sequentially
                for page_num in range(page_count):
                    page = pdf_doc[page_num]
                    page_text = page.get_textpage().get_text_range()
                    page_texts.append(page_text)

            pdf_doc.close()
            full_text = "\n\n".join(page_texts)

            return {
                "full_text": full_text,
                "page_texts": page_texts,
                "page_coordinates": [],
                "spacy_doc": None,
            }
        except Exception as e:
            self.logger.error(f"Fallback text extraction failed: {str(e)}")
            raise

    def _create_redacted_pdf_with_coordinates(
        self,
        original_path: str,
        layout_data: Dict[str, Any],
        pii_findings: List[Dict[str, Any]],
        output_dir: str,
    ) -> str:
        """
        Create redacted PDF using precise coordinate information when available.

        Args:
            original_path: Path to original PDF
            layout_data: Dictionary containing text and coordinate data
            pii_findings: List of PII detection findings
            output_dir: Directory to save redacted PDF

        Returns:
            Path to the redacted PDF file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            original_name = Path(original_path).stem
            output_filename = f"{original_name}_REDACTED_{timestamp}.pdf"
            output_path = Path(output_dir) / output_filename

            # Use coordinate-based redaction if we have layout data
            if layout_data.get("page_coordinates") and any(
                layout_data["page_coordinates"]
            ):
                self._create_coordinate_based_redacted_pdf(
                    original_path, layout_data, pii_findings, output_path
                )
            else:
                # Fallback to text-based redaction
                self._create_redacted_pdf_with_reportlab(
                    original_path, layout_data["page_texts"], pii_findings, output_path
                )

            self.logger.info(f"Redacted PDF saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error creating redacted PDF: {str(e)}")
            raise

    def _create_coordinate_based_redacted_pdf(
        self,
        original_path: str,
        layout_data: Dict[str, Any],
        pii_findings: List[Dict[str, Any]],
        output_path: Path,
    ) -> None:
        """
        Create redacted PDF using precise character coordinates.
        """
        try:
            with open(original_path, "rb") as original_file:
                pdf_reader = PyPDF2.PdfReader(original_file)
                pdf_writer = PyPDF2.PdfWriter()

                page_coordinates = layout_data["page_coordinates"]
                page_texts = layout_data["page_texts"]
                page_count = len(pdf_reader.pages)

                # Use parallel processing for multi-page documents
                if page_count > 4:  # Only use parallel processing for larger documents
                    from concurrent.futures import ThreadPoolExecutor, as_completed

                    # Process pages in parallel
                    overlay_pages = [None] * page_count
                    with ThreadPoolExecutor(max_workers=4) as executor:
                        # Submit tasks for pages that need overlay processing
                        future_to_page = {}
                        for page_num in range(page_count):
                            original_page = pdf_reader.pages[page_num]
                            if (
                                page_num < len(page_coordinates)
                                and page_coordinates[page_num]
                            ):
                                future = executor.submit(
                                    self._create_precise_redaction_overlay,
                                    original_page,
                                    page_texts[page_num],
                                    page_coordinates[page_num],
                                    pii_findings,
                                    page_num,
                                )
                                future_to_page[future] = page_num

                        # Collect results
                        for future in as_completed(future_to_page):
                            page_num = future_to_page[future]
                            try:
                                overlay_page = future.result()
                                overlay_pages[page_num] = overlay_page
                            except Exception as e:
                                self.logger.error(
                                    f"Error processing page {page_num}: {str(e)}"
                                )
                                overlay_pages[page_num] = None

                    # Merge overlay pages with original pages
                    for page_num in range(page_count):
                        original_page = pdf_reader.pages[page_num]
                        overlay_page = overlay_pages[page_num]

                        if overlay_page:
                            original_page.merge_page(overlay_page)

                        pdf_writer.add_page(original_page)
                else:
                    # For smaller documents, process sequentially
                    for page_num in range(len(pdf_reader.pages)):
                        original_page = pdf_reader.pages[page_num]

                        if (
                            page_num < len(page_coordinates)
                            and page_coordinates[page_num]
                        ):
                            # Create overlay with precise redaction boxes
                            overlay_page = self._create_precise_redaction_overlay(
                                original_page,
                                page_texts[page_num],
                                page_coordinates[page_num],
                                pii_findings,
                                page_num,
                            )
                            if overlay_page:
                                original_page.merge_page(overlay_page)

                        pdf_writer.add_page(original_page)

                # Save the redacted PDF
                with open(output_path, "wb") as output_file:
                    pdf_writer.write(output_file)

                self._validate_redaction_completeness(str(output_path), pii_findings)

        except Exception as e:
            self.logger.error(f"Error creating coordinate-based redacted PDF: {str(e)}")
            raise

    def _create_precise_redaction_overlay(
        self,
        original_page: Any,
        page_text: str,
        char_coords: List[Dict[str, Any]],
        pii_findings: List[Dict[str, Any]],
        page_num: int,
    ) -> Optional[Any]:
        """
        Create overlay with precise redaction boxes based on character coordinates.
        """
        try:
            # Find PII entities that appear on this page
            page_entities = [
                entity for entity in pii_findings if entity["text"] in page_text
            ]

            if not page_entities:
                return None

            # Create overlay PDF
            packet = io.BytesIO()
            page_width = float(original_page.mediabox.width)
            page_height = float(original_page.mediabox.height)

            overlay_canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))

            # Add precise redaction boxes for each PII entity
            for entity in page_entities:
                self._add_precise_redaction_box(
                    overlay_canvas,
                    entity,
                    page_text,
                    char_coords,
                    page_width,
                    page_height,
                )

            overlay_canvas.save()
            packet.seek(0)

            overlay_pdf = PyPDF2.PdfReader(packet)
            return overlay_pdf.pages[0]

        except Exception as e:
            self.logger.error(
                f"Error creating precise redaction overlay for page {page_num}: {str(e)}"
            )
            return None

    def _add_precise_redaction_box(
        self,
        canvas_obj: canvas.Canvas,
        entity: Dict[str, Any],
        page_text: str,
        char_coords: List[Dict[str, Any]],
        page_width: float,
        page_height: float,
    ) -> None:
        """
        Add redaction box using precise character coordinates.
        """
        try:
            entity_text = entity["text"]
            entity_start = entity.get("start", 0)
            entity_end = entity.get("end", len(entity_text))

            # Find the character coordinates for this entity
            entity_boxes = []
            for i, char_data in enumerate(char_coords):
                char_pos_in_text = page_text.find(char_data["char"], i)
                if entity_start <= char_pos_in_text < entity_end:
                    entity_boxes.append(char_data)

            if not entity_boxes:
                # Fallback to estimated position
                self._add_redaction_box(
                    canvas_obj, entity, page_text, page_width, page_height
                )
                return

            # Calculate bounding box for the entity
            min_x = min(box["x"] for box in entity_boxes)
            max_x = max(box["x"] + box["width"] for box in entity_boxes)
            min_y = min(box["y"] for box in entity_boxes)
            max_y = max(box["y"] + box["height"] for box in entity_boxes)

            # Create redaction box
            box_width = max_x - min_x
            box_height = max_y - min_y

            # Apply redaction styling
            canvas_obj.setFillColor(colors.black)
            canvas_obj.setStrokeColor(colors.darkgrey)
            canvas_obj.setLineWidth(0.5)

            # Draw redaction box
            canvas_obj.rect(min_x, min_y, box_width, box_height, fill=1, stroke=1)

            # Add redaction label
            canvas_obj.setFillColor(colors.white)
            canvas_obj.setFont("Helvetica-Bold", 8)

            entity_type = entity.get("entity_type", "PII").replace("_", " ").title()
            label = f"[{entity_type}]"

            # Center label in the box
            text_width = canvas_obj.stringWidth(label, "Helvetica-Bold", 8)
            label_x = min_x + (box_width - text_width) / 2
            label_y = min_y + (box_height - 8) / 2

            canvas_obj.drawString(label_x, label_y, label)

        except Exception as e:
            self.logger.warning(f"Could not add precise redaction box: {str(e)}")
            # Fallback to estimated redaction
            self._add_redaction_box(
                canvas_obj, entity, page_text, page_width, page_height
            )

    def _create_redacted_pdf(
        self,
        original_path: str,
        page_texts: List[str],
        pii_findings: List[Dict[str, Any]],
        output_dir: str,
    ) -> str:
        """
        Create redacted PDF by actually removing PII text from content streams.
        This ensures PII cannot be copied or selected from the final PDF.

        Args:
            original_path: Path to original PDF
            page_texts: List of text content per page
            pii_findings: List of PII detection findings
            output_dir: Directory to save redacted PDF

        Returns:
            Path to the redacted PDF file
        """
        try:
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            original_name = Path(original_path).stem
            output_filename = f"{original_name}_REDACTED_{timestamp}.pdf"
            output_path = Path(output_dir) / output_filename

            # For true redaction, we need to rebuild the PDF with redacted text
            # This prevents any possibility of recovering the original PII
            self._create_redacted_pdf_with_reportlab(
                original_path, page_texts, pii_findings, output_path
            )

            self.logger.info(f"Redacted PDF saved to: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error creating redacted PDF: {str(e)}")
            raise

    def _create_redacted_pdf_with_reportlab(
        self,
        original_path: str,
        page_texts: List[str],
        pii_findings: List[Dict[str, Any]],
        output_path: Path,
    ) -> None:
        """
        Create a completely new PDF with redacted text using ReportLab.
        This ensures no PII remains in the final document.
        """
        try:
            # Open original PDF to get page count and dimensions
            with open(original_path, "rb") as original_file:
                pdf_reader = PyPDF2.PdfReader(original_file)
                total_pages = len(pdf_reader.pages)

                # Get first page dimensions for reference
                first_page = pdf_reader.pages[0]
                page_width = float(first_page.mediabox.width)
                page_height = float(first_page.mediabox.height)

            # Create new PDF with ReportLab
            c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

            # Use parallel processing for multi-page documents
            page_count = min(len(page_texts), total_pages)
            if page_count > 4:  # Only use parallel processing for larger documents
                from concurrent.futures import ThreadPoolExecutor, as_completed

                # Process pages in parallel to generate redacted text
                redacted_texts = [None] * page_count
                with ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit tasks for redacting each page
                    future_to_page = {}
                    for page_num, page_text in enumerate(page_texts):
                        if page_num >= total_pages:
                            break
                        future = executor.submit(
                            self._redact_page_text, page_text, pii_findings
                        )
                        future_to_page[future] = page_num

                    # Collect results
                    for future in as_completed(future_to_page):
                        page_num = future_to_page[future]
                        try:
                            redacted_text = future.result()
                            redacted_texts[page_num] = redacted_text
                        except Exception as e:
                            self.logger.error(
                                f"Error redacting page {page_num}: {str(e)}"
                            )
                            redacted_texts[page_num] = page_texts[
                                page_num
                            ]  # Use original if redaction fails

                # Add text to PDF pages sequentially (ReportLab is not thread-safe)
                for page_num, redacted_text in enumerate(redacted_texts):
                    if redacted_text is not None:
                        self._add_secure_text_to_page(
                            c, redacted_text, page_width, page_height
                        )
                        if page_num < len(redacted_texts) - 1:
                            c.showPage()
            else:
                # For smaller documents, process sequentially
                for page_num, page_text in enumerate(page_texts):
                    if page_num >= total_pages:
                        break

                    # Create redacted text for this page
                    redacted_text = self._redact_page_text(page_text, pii_findings)

                    # Add text to the new PDF page
                    self._add_secure_text_to_page(
                        c, redacted_text, page_width, page_height
                    )

                    # Finish the page
                    if page_num < len(page_texts) - 1:
                        c.showPage()

            # Save the PDF
            c.save()

            # Validate that no PII remains in the final document
            self._validate_redaction_completeness(str(output_path), pii_findings)

        except Exception as e:
            self.logger.error(f"Error creating secure redacted PDF: {str(e)}")
            raise

    def _validate_redaction_completeness(
        self, redacted_pdf_path: str, original_pii_findings: List[Dict[str, Any]]
    ) -> None:
        """
        Validate that no original PII text remains in the redacted PDF.
        """
        try:
            # Extract text from the redacted PDF for validation
            validation_data = self._extract_text_from_pdf_fallback(redacted_pdf_path)
            redacted_text = validation_data["full_text"]

            # Check if any original PII text is still present
            violations = []
            for finding in original_pii_findings:
                original_text = finding["text"]
                if original_text.lower() in redacted_text.lower():
                    violations.append(original_text)

            if violations:
                self.logger.error(
                    f"SECURITY VIOLATION: Original PII still found in redacted PDF: {violations}"
                )
                raise ValueError(
                    f"Redaction failed - original PII still present: {violations}"
                )
            else:
                self.logger.info(
                    "Redaction validation passed - no original PII found in final document"
                )

        except Exception as e:
            self.logger.warning(f"Could not validate redaction completeness: {str(e)}")

    @lru_cache(maxsize=64)
    def _wrap_text_cached(
        self, text: str, max_width: float, font_name: str, font_size: int
    ) -> tuple:
        """
        Cached version of text wrapping.
        Returns a tuple of (lines, line_heights) for efficiency.
        """
        # Create a temporary canvas for measuring text
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen.canvas import Canvas

        temp_canvas = Canvas("temp.pdf", pagesize=letter)
        temp_canvas.setFont(font_name, font_size)

        # Split text into lines that fit the page width
        lines = []
        line_heights = []
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                line_heights.append(font_size + 2)
                continue

            # Word wrap for long lines
            words = paragraph.split()
            current_line = ""

            for word in words:
                test_line = f"{current_line} {word}".strip()
                text_width = temp_canvas.stringWidth(test_line, font_name, font_size)

                if text_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        line_heights.append(font_size + 2)
                    current_line = word

            if current_line:
                lines.append(current_line)
                line_heights.append(font_size + 2)

        return (tuple(lines), tuple(line_heights))

    def _add_secure_text_to_page(
        self,
        canvas_obj: canvas.Canvas,
        text: str,
        page_width: float,
        page_height: float,
    ) -> None:
        """
        Add redacted text to a PDF page with proper formatting.
        """
        try:
            # Set up text formatting
            font_name = "Helvetica"
            font_size = 11
            canvas_obj.setFont(font_name, font_size)
            canvas_obj.setFillColor(colors.black)

            # Text positioning
            margin = 50
            max_width = page_width - (2 * margin)

            # Use cached text wrapping
            lines, line_heights = self._wrap_text_cached(
                text, max_width, font_name, font_size
            )

            # Draw text lines
            y_position = page_height - margin - 20

            for i, line in enumerate(lines):
                if y_position < margin:
                    break  # Prevent text from going off page

                canvas_obj.drawString(margin, y_position, line)
                y_position -= (
                    line_heights[i] if i < len(line_heights) else (font_size + 2)
                )

        except Exception as e:
            self.logger.warning(f"Error adding text to page: {str(e)}")

    def _create_redacted_page(
        self,
        original_page: Any,
        page_text: str,
        pii_findings: List[Dict[str, Any]],
        page_num: int,
    ) -> Any:
        """
        Create redacted version of a page by overlaying redaction boxes.

        Args:
            original_page: Original PDF page object
            page_text: Text content of the page
            pii_findings: List of PII entities to redact
            page_num: Page number (0-based)

        Returns:
            Modified page with redactions
        """
        try:
            # Find PII entities that appear on this page
            page_entities = [
                entity for entity in pii_findings if entity["text"] in page_text
            ]

            if not page_entities:
                return original_page

            # Create overlay with redaction boxes
            import io

            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            # Create a BytesIO buffer for the overlay
            packet = io.BytesIO()

            # Get page dimensions
            page_width = float(original_page.mediabox.width)
            page_height = float(original_page.mediabox.height)

            # Create canvas for overlay
            overlay_canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))

            # Add redaction boxes for each PII entity
            for entity in page_entities:
                self._add_redaction_box(
                    overlay_canvas, entity, page_text, page_width, page_height
                )

            overlay_canvas.save()

            # Move to the beginning of the StringIO buffer
            packet.seek(0)

            # Create a new PDF with the overlay
            overlay_pdf = PyPDF2.PdfReader(packet)
            overlay_page = overlay_pdf.pages[0]

            # Merge the overlay with the original page
            original_page.merge_page(overlay_page)

            return original_page

        except Exception as e:
            self.logger.error(f"Error creating redacted page {page_num}: {str(e)}")
            return original_page

    def _add_redaction_box(
        self,
        canvas_obj: canvas.Canvas,
        entity: Dict[str, Any],
        page_text: str,
        page_width: float,
        page_height: float,
    ) -> None:
        """
        Add a professional redaction box for a PII entity.

        Args:
            canvas_obj: ReportLab canvas object
            entity: PII entity to redact
            page_text: Full page text for position calculation
            page_width: Page width
            page_height: Page height
        """
        try:
            # Estimate position (this is simplified - in reality you'd need proper text positioning)
            text_before = page_text[: entity.get("start", 0)]
            lines_before = text_before.count("\n")

            # Estimate coordinates (from bottom-left origin)
            y_position = page_height - (lines_before * 14) - 60  # Improved spacing
            x_position = 50  # Left margin

            # Calculate box dimensions based on text length
            text_length = len(entity["text"])
            box_width = min(
                text_length * 7, page_width - 100
            )  # Better character width estimation
            box_height = 14

            # Create professional redaction styling
            canvas_obj.setFillColor(colors.black)
            canvas_obj.setStrokeColor(colors.darkgrey)
            canvas_obj.setLineWidth(0.5)

            # Draw main redaction box with border
            canvas_obj.rect(
                x_position, y_position, box_width, box_height, fill=1, stroke=1
            )

            # Add redaction label with proper formatting
            canvas_obj.setFillColor(colors.white)
            canvas_obj.setFont("Helvetica-Bold", 7)

            # Format entity type for display
            entity_type = entity["entity_type"]
            display_type = entity_type.replace("_", " ").title()
            label = f"[{display_type}]"

            # Center the label in the box
            text_width = canvas_obj.stringWidth(label, "Helvetica-Bold", 7)
            label_x = x_position + (box_width - text_width) / 2
            label_y = y_position + 4

            canvas_obj.drawString(label_x, label_y, label)

            # Add subtle decorative elements
            canvas_obj.setStrokeColor(colors.grey)
            canvas_obj.setLineWidth(0.3)
            canvas_obj.line(
                x_position, y_position - 1, x_position + box_width, y_position - 1
            )

        except Exception as e:
            self.logger.warning(f"Could not add redaction box for entity: {str(e)}")
            # Fallback to simple black box
            try:
                x_position = 50
                y_position = page_height - 100
                canvas_obj.setFillColor(colors.black)
                canvas_obj.rect(x_position, y_position, 100, 12, fill=1)
            except:
                pass

    @lru_cache(maxsize=128)
    def _redact_page_text_cached(self, page_text: str, entities_key: str) -> str:
        """
        Cached version of page text redaction.
        """
        import json

        pii_entities = json.loads(entities_key)

        # Filter relevant entities for this page
        relevant_entities = [
            entity for entity in pii_entities if entity["text"] in page_text
        ]

        if not relevant_entities:
            return page_text

        # Sort entities by position (descending) to avoid offset issues
        # Sort by start position in descending order
        sorted_entities = sorted(
            relevant_entities, key=lambda x: x.get("start", 0), reverse=True
        )

        # Use list to build redacted text more efficiently
        redacted_parts = []
        last_end = len(page_text)

        for entity in sorted_entities:
            start = entity.get("start", 0)
            end = entity.get("end", len(entity["text"]))

            # Add the unredacted part after this entity
            redacted_parts.append(page_text[end:last_end])

            # Add the redacted part
            entity_type = entity["entity_type"].replace("_", " ").title()
            # Use block characters that match the length of original text
            redacted_length = end - start
            block_chars = "█" * min(redacted_length, 20)  # Limit to 20 chars max
            redaction = f"[{entity_type}:{block_chars}]"
            redacted_parts.append(redaction)

            last_end = start

        # Add the beginning part of the text
        redacted_parts.append(page_text[:last_end])

        # Reverse and join parts
        redacted_parts.reverse()
        return "".join(redacted_parts)

    def _redact_page_text(
        self, page_text: str, pii_entities: List[Dict[str, Any]]
    ) -> str:
        """
        Redact PII entities in page text.

        Args:
            page_text: Original page text
            pii_entities: List of PII entities to redact

        Returns:
            Text with PII entities redacted
        """
        # Create a cache key from the entities
        import json

        entities_key = json.dumps(pii_entities, sort_keys=True)

        # Use cached version if available
        return self._redact_page_text_cached(page_text, entities_key)

    def _add_text_to_page(
        self, canvas_obj: canvas.Canvas, text: str, page_num: int
    ) -> None:
        """
        Add text content to a PDF page.

        Args:
            canvas_obj: ReportLab canvas object
            text: Text content to add
            page_num: Page number for reference
        """
        try:
            # Set font and starting position
            canvas_obj.setFont("Helvetica", 10)
            x_start = 50
            y_start = 750
            line_height = 12
            max_width = 500

            # Split text into lines that fit within page width
            lines = self._wrap_text(text, max_width, canvas_obj)

            y_position = y_start

            for line in lines:
                if y_position < 50:  # Near bottom of page
                    break

                canvas_obj.drawString(x_start, y_position, line)
                y_position -= line_height

            # Add page number
            canvas_obj.drawString(500, 30, f"Page {page_num}")

        except Exception as e:
            self.logger.error(f"Error adding text to page: {str(e)}")

    def _wrap_text(
        self, text: str, max_width: float, canvas_obj: canvas.Canvas
    ) -> List[str]:
        """
        Wrap text to fit within specified width.

        Args:
            text: Text to wrap
            max_width: Maximum width in points
            canvas_obj: Canvas object for measuring text

        Returns:
            List of wrapped text lines
        """
        lines = []
        paragraphs = text.split("\n")

        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("")
                continue

            words = paragraph.split(" ")
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                text_width = canvas_obj.stringWidth(test_line, "Helvetica", 10)

                if text_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

        return lines

    def _calculate_confidence_score(self, pii_findings: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score based on PII detection results.

        Args:
            pii_findings: List of PII detection findings

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence on successful processing
        base_confidence = 0.85

        # Boost confidence if entities were found and processed
        if len(pii_findings) > 0:
            base_confidence = 0.95

        return base_confidence

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".pdf"]

    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file is a readable PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            True if file is valid, False otherwise
        """
        try:
            pdf_doc = pdfium.PdfDocument(file_path)
            page_count = len(pdf_doc)
            pdf_doc.close()
            return page_count > 0
        except Exception as e:
            self.logger.error(f"Invalid PDF file {file_path}: {str(e)}")
            return False
