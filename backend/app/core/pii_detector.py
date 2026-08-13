"""
PII (Personally Identifiable Information) Detector
Enhanced for spaCy Layout integration with precise positioning
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PIIDetector:
    """
    Comprehensive PII detection using multiple approaches:
    1. Regex patterns for common PII types
    2. spaCy Layout integration for position-aware detection
    3. Layout span analysis for precise redaction
    """
    
    def __init__(self):
        self.spacy_model = None
        self.presidio_analyzer = None
        self._initialize_detectors()
        
        # Enhanced regex patterns with capture groups for better precision
        self.regex_patterns = {
            'EMAIL_ADDRESS': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'PHONE_NUMBER': re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
            'SSN': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'CREDIT_CARD': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'IP_ADDRESS': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'URL': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            'DATE_OF_BIRTH': re.compile(r'\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12][0-9]|3[01])[/-](19|20)\d{2}\b'),
            'PASSPORT_NUMBER': re.compile(r'\b[A-Z]{1,2}[0-9]{6,9}\b'),
            'LICENSE_PLATE': re.compile(r'\b[A-Z]{2,3}[-\s]?[0-9]{3,4}[-\s]?[A-Z]?\b'),
        }
    
    def detect_pii_with_layout(self, spacy_doc: Any) -> Dict[str, Any]:
        """
        Detect PII in spaCy document with layout information.
        
        Args:
            spacy_doc: Processed spaCy document with layout spans
            
        Returns:
            Dictionary with detected entities and their layout positions
        """
        try:
            full_text = spacy_doc.text
            layout_spans = spacy_doc.spans.get("layout", [])
            
            # Detect PII in full text first
            text_entities = self._detect_with_regex(full_text)
            
            # Map entities to layout spans for precise positioning
            layout_entities = []
            for entity in text_entities:
                span_info = self._find_entity_span(entity, layout_spans)
                if span_info:
                    entity.update(span_info)
                    layout_entities.append(entity)
            
            # Calculate statistics
            entity_types = {}
            for entity in layout_entities:
                pii_type = entity['type']
                entity_types[pii_type] = entity_types.get(pii_type, 0) + 1
            
            # Generate redacted text
            redacted_text = self._create_redacted_text(full_text, layout_entities)
            
            result = {
                'entities': layout_entities,
                'total_entities': len(layout_entities),
                'entity_types': entity_types,
                'redacted_text': redacted_text,
                'original_length': len(full_text),
                'redacted_length': len(redacted_text),
                'layout_spans_analyzed': len(layout_spans)
            }
            
            logger.info(f"Layout-aware PII detection completed: {len(layout_entities)} entities found")
            return result
            
        except Exception as e:
            logger.error(f"Error in layout-aware PII detection: {str(e)}")
            raise
    
    def _find_entity_span(
        self, 
        entity: Dict[str, Any], 
        layout_spans: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the layout span that contains a detected PII entity.
        
        Args:
            entity: Detected PII entity with start/end positions
            layout_spans: List of layout spans from spaCy processing
            
        Returns:
            Dictionary with span information or None if not found
        """
        entity_start = entity['start']
        entity_end = entity['end']
        
        for span in layout_spans:
            span_start = span.start_char
            span_end = span.end_char
            
            # Check if entity is within this span
            if span_start <= entity_start < span_end and span_start < entity_end <= span_end:
                span_info = {
                    'span_id': getattr(span, 'id', None),
                    'span_label': span.label_,
                    'span_start_char': span_start,
                    'span_end_char': span_end,
                }
                
                # Add layout information if available
                if hasattr(span, '_') and hasattr(span._, 'layout') and span._.layout:
                    layout = span._.layout
                    span_info.update({
                        'bounding_box': {
                            'x': layout.x,
                            'y': layout.y,
                            'width': layout.width,
                            'height': layout.height,
                            'page_no': layout.page_no
                        }
                    })
                
                return span_info
        
        return None
    
    def _initialize_detectors(self):
        """Initialize spaCy and Presidio detectors"""
        try:
            # Use regex-only detection for now to avoid model download issues
            logger.info("Using regex-only PII detection to avoid network dependencies")
            self.spacy_model = None
            self.presidio_analyzer = None
                
        except Exception as e:
            logger.error(f"Error initializing PII detectors: {str(e)}")
            # Fall back to regex-only detection
    
    def _detect_with_regex(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII using regex patterns"""
        findings = []
        
        for pii_type, pattern in self.regex_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                findings.append({
                    'entity_type': pii_type,
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group(),
                    'confidence': 0.9,  # High confidence for regex matches
                    'detection_method': 'regex'
                })
        
        return findings
    
    def _detect_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII using spaCy named entity recognition"""
        if not self.spacy_model:
            return []
            
        findings = []
        
        try:
            doc = self.spacy_model(text)
            
            for ent in doc.ents:
                # Map spaCy entity types to our PII types
                entity_mapping = {
                    'PERSON': 'PERSON',
                    'ORG': 'ORGANIZATION',
                    'GPE': 'LOCATION',  # Geopolitical entity
                    'LOC': 'LOCATION',
                    'DATE': 'DATE_TIME',
                    'TIME': 'DATE_TIME',
                    'MONEY': 'FINANCIAL',
                    'CARDINAL': 'NUMBER',
                    'ORDINAL': 'NUMBER'
                }
                
                pii_type = entity_mapping.get(ent.label_, ent.label_)
                
                # Only include relevant PII types
                if pii_type in ['PERSON', 'ORGANIZATION', 'LOCATION', 'DATE_TIME']:
                    findings.append({
                        'entity_type': pii_type,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'text': ent.text,
                        'confidence': 0.8,  # Good confidence for NLP
                        'detection_method': 'spacy',
                        'label': ent.label_
                    })
                    
        except Exception as e:
            logger.error(f"Error in spaCy detection: {str(e)}")
        
        return findings
    
    def _detect_with_presidio(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII using Presidio analyzer"""
        if not self.presidio_analyzer:
            return []
            
        findings = []
        
        try:
            # Analyze text with Presidio
            results = self.presidio_analyzer.analyze(text=text, language='en')
            
            for result in results:
                findings.append({
                    'entity_type': result.entity_type,
                    'start': result.start,
                    'end': result.end,
                    'text': text[result.start:result.end],
                    'confidence': result.score,
                    'detection_method': 'presidio'
                })
                
        except Exception as e:
            logger.error(f"Error in Presidio detection: {str(e)}")
        
        return findings
    
    def _merge_overlapping_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping PII findings and keep the highest confidence"""
        if not findings:
            return []
        
        # Sort by start position
        sorted_findings = sorted(findings, key=lambda x: x['start'])
        merged = []
        
        for finding in sorted_findings:
            if not merged:
                merged.append(finding)
                continue
            
            last = merged[-1]
            
            # Check for overlap
            if finding['start'] <= last['end']:
                # Overlapping - keep the one with higher confidence
                if finding['confidence'] > last['confidence']:
                    merged[-1] = finding
                # If same confidence, prefer more specific detection method
                elif finding['confidence'] == last['confidence']:
                    method_priority = {'presidio': 3, 'spacy': 2, 'regex': 1}
                    if method_priority.get(finding['detection_method'], 0) > method_priority.get(last['detection_method'], 0):
                        merged[-1] = finding
            else:
                merged.append(finding)
        
        return merged
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Main PII detection method - combines all detection approaches
        
        Args:
            text: Text to analyze for PII
            
        Returns:
            List of PII findings with metadata
        """
        if not text or not text.strip():
            return []
        
        all_findings = []
        
        # 1. Regex detection (fastest, most reliable for structured data)
        regex_findings = self._detect_with_regex(text)
        all_findings.extend(regex_findings)
        
        # 2. spaCy detection (good for names, organizations)
        spacy_findings = self._detect_with_spacy(text)
        all_findings.extend(spacy_findings)
        
        # 3. Presidio detection (comprehensive enterprise patterns)
        presidio_findings = self._detect_with_presidio(text)
        all_findings.extend(presidio_findings)
        
        # Merge overlapping findings
        merged_findings = self._merge_overlapping_findings(all_findings)
        
        return merged_findings
    
    def get_detector_status(self) -> Dict[str, bool]:
        """Get status of all detection methods"""
        return {
            'regex': True,  # Always available
            'spacy': self.spacy_model is not None,
            'presidio': self.presidio_analyzer is not None
        }