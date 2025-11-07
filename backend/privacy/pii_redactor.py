"""
PII Redaction Module
Detects and redacts personally identifying information using NER and regex patterns.
"""

import re
import logging
from typing import Tuple, Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import spaCy
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
        logger.info("✓ spaCy model loaded successfully")
    except OSError:
        logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
        nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None
    logger.warning("spaCy not available. Using regex-only PII detection.")


class PIIRedactor:
    """
    Detects and redacts PII from text using NER and regex patterns.
    """
    
    # Regex patterns for PII detection
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    )
    
    PHONE_PATTERNS = [
        re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),  # 123-456-7890, 123.456.7890, 1234567890
        re.compile(r'\(\d{3}\)\s*\d{3}[-.]?\d{4}\b'),  # (123) 456-7890
        re.compile(r'\+\d{1,3}\s?\d{3}[-.]?\d{3}[-.]?\d{4}\b'),  # +1 123-456-7890
    ]
    
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')  # 123-45-6789
    
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    
    # Common ID patterns
    ID_PATTERNS = [
        re.compile(r'\b[A-Z]{2}\d{6,8}\b'),  # Passport-like: AB1234567
        re.compile(r'\bID[-\s]?\d{6,10}\b', re.IGNORECASE),  # ID-123456789
    ]
    
    # IP Address pattern
    IP_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    
    def __init__(self, use_spacy: bool = True):
        """
        Initialize PII redactor.
        
        Args:
            use_spacy: Whether to use spaCy NER (if available)
        """
        self.use_spacy = use_spacy and SPACY_AVAILABLE and nlp is not None
        self.entity_counters = defaultdict(int)
        
        if not self.use_spacy:
            logger.warning("Operating in regex-only mode. Install spaCy for better accuracy.")
    
    def redact_pii(self, text: str, preserve_structure: bool = True) -> Tuple[str, Dict]:
        """
        Detect and redact PII from text.
        
        Args:
            text: Input text that may contain PII
            preserve_structure: If True, replace with placeholders. If False, remove entirely.
            
        Returns:
            Tuple of (redacted_text, pii_metadata)
            
        Example:
            >>> redactor = PIIRedactor()
            >>> redacted, metadata = redactor.redact_pii("John Doe (john@example.com) called 555-1234")
            >>> print(redacted)
            "[NAME_1] ([EMAIL_1]) called [PHONE_1]"
            >>> print(metadata)
            {"names": 1, "emails": 1, "phones": 1, "placeholders": {...}}
        """
        if not text:
            return "", {"total_redactions": 0}
        
        # Reset counters for this redaction
        self.entity_counters.clear()
        
        redacted_text = text
        pii_metadata = {
            "names": 0,
            "emails": 0,
            "phones": 0,
            "locations": 0,
            "organizations": 0,
            "ssn": 0,
            "credit_cards": 0,
            "ids": 0,
            "ip_addresses": 0,
            "placeholders": {},
            "total_redactions": 0
        }
        
        # Step 1: Redact using regex patterns (high confidence)
        redacted_text, pii_metadata = self._redact_with_regex(redacted_text, pii_metadata)
        
        # Step 2: Use spaCy NER if available
        if self.use_spacy:
            redacted_text, pii_metadata = self._redact_with_spacy(redacted_text, pii_metadata)
        
        pii_metadata["total_redactions"] = sum(
            v for k, v in pii_metadata.items() 
            if k not in ["placeholders", "total_redactions"] and isinstance(v, int)
        )
        
        return redacted_text, pii_metadata
    
    def _redact_with_regex(self, text: str, metadata: Dict) -> Tuple[str, Dict]:
        """Redact PII using regex patterns."""
        
        # Track replacements to avoid double-counting
        replacements = []
        
        # Emails
        for match in self.EMAIL_PATTERN.finditer(text):
            email = match.group()
            self.entity_counters["email"] += 1
            placeholder = f"[EMAIL_{self.entity_counters['email']}]"
            replacements.append((match.start(), match.end(), placeholder, "emails"))
            metadata["placeholders"][placeholder] = "email"
        
        # Phone numbers
        for pattern in self.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                phone = match.group()
                self.entity_counters["phone"] += 1
                placeholder = f"[PHONE_{self.entity_counters['phone']}]"
                replacements.append((match.start(), match.end(), placeholder, "phones"))
                metadata["placeholders"][placeholder] = "phone"
        
        # SSN
        for match in self.SSN_PATTERN.finditer(text):
            self.entity_counters["ssn"] += 1
            placeholder = f"[SSN_{self.entity_counters['ssn']}]"
            replacements.append((match.start(), match.end(), placeholder, "ssn"))
            metadata["placeholders"][placeholder] = "ssn"
        
        # Credit cards
        for match in self.CREDIT_CARD_PATTERN.finditer(text):
            # Verify it looks like a credit card (not just random numbers)
            digits = re.sub(r'[-\s]', '', match.group())
            if len(digits) == 16:
                self.entity_counters["credit_card"] += 1
                placeholder = f"[CC_{self.entity_counters['credit_card']}]"
                replacements.append((match.start(), match.end(), placeholder, "credit_cards"))
                metadata["placeholders"][placeholder] = "credit_card"
        
        # IDs
        for pattern in self.ID_PATTERNS:
            for match in pattern.finditer(text):
                self.entity_counters["id"] += 1
                placeholder = f"[ID_{self.entity_counters['id']}]"
                replacements.append((match.start(), match.end(), placeholder, "ids"))
                metadata["placeholders"][placeholder] = "id"
        
        # IP addresses
        for match in self.IP_PATTERN.finditer(text):
            # Basic validation (all octets < 256)
            octets = [int(x) for x in match.group().split('.')]
            if all(0 <= o <= 255 for o in octets):
                self.entity_counters["ip"] += 1
                placeholder = f"[IP_{self.entity_counters['ip']}]"
                replacements.append((match.start(), match.end(), placeholder, "ip_addresses"))
                metadata["placeholders"][placeholder] = "ip"
        
        # Sort replacements by position (reverse) to avoid index shifting
        replacements.sort(key=lambda x: x[0], reverse=True)
        
        # Apply replacements
        for start, end, placeholder, category in replacements:
            text = text[:start] + placeholder + text[end:]
            metadata[category] += 1
        
        return text, metadata
    
    def _redact_with_spacy(self, text: str, metadata: Dict) -> Tuple[str, Dict]:
        """Redact PII using spaCy NER."""
        if not nlp:
            return text, metadata
        
        try:
            doc = nlp(text)
            replacements = []
            
            for ent in doc.ents:
                # Names (PERSON)
                if ent.label_ == "PERSON":
                    self.entity_counters["name"] += 1
                    placeholder = f"[NAME_{self.entity_counters['name']}]"
                    replacements.append((ent.start_char, ent.end_char, placeholder, "names"))
                    metadata["placeholders"][placeholder] = "name"
                
                # Locations (GPE, LOC)
                elif ent.label_ in ["GPE", "LOC"]:
                    self.entity_counters["location"] += 1
                    placeholder = f"[LOCATION_{self.entity_counters['location']}]"
                    replacements.append((ent.start_char, ent.end_char, placeholder, "locations"))
                    metadata["placeholders"][placeholder] = "location"
                
                # Organizations
                elif ent.label_ == "ORG":
                    self.entity_counters["org"] += 1
                    placeholder = f"[ORG_{self.entity_counters['org']}]"
                    replacements.append((ent.start_char, ent.end_char, placeholder, "organizations"))
                    metadata["placeholders"][placeholder] = "organization"
            
            # Sort and apply replacements (reverse order)
            replacements.sort(key=lambda x: x[0], reverse=True)
            
            for start, end, placeholder, category in replacements:
                text = text[:start] + placeholder + text[end:]
                metadata[category] += 1
            
        except Exception as e:
            logger.error(f"spaCy NER failed: {e}")
        
        return text, metadata
    
    def validate_redaction(self, original: str, redacted: str) -> bool:
        """
        Validate that redaction was successful (no obvious PII remains).
        
        Args:
            original: Original text
            redacted: Redacted text
            
        Returns:
            True if validation passes, False if potential PII remains
        """
        # Quick checks for common PII patterns
        if self.EMAIL_PATTERN.search(redacted):
            logger.warning("Email pattern detected in redacted text")
            return False
        
        for pattern in self.PHONE_PATTERNS:
            if pattern.search(redacted):
                logger.warning("Phone pattern detected in redacted text")
                return False
        
        if self.SSN_PATTERN.search(redacted):
            logger.warning("SSN pattern detected in redacted text")
            return False
        
        return True


# Singleton instance
_redactor_instance = None

def get_pii_redactor(use_spacy: bool = True) -> PIIRedactor:
    """Get or create singleton PII redactor instance."""
    global _redactor_instance
    if _redactor_instance is None:
        _redactor_instance = PIIRedactor(use_spacy=use_spacy)
    return _redactor_instance


def redact_pii(text: str) -> Tuple[str, Dict]:
    """
    Convenience function to redact PII from text.
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (redacted_text, pii_metadata)
    """
    redactor = get_pii_redactor()
    return redactor.redact_pii(text)
