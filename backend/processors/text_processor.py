"""
Text Processing Module
PII detection/redaction, tokenization, and embedding generation
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Try to import NLP libraries
try:
    import spacy
    SPACY_AVAILABLE = True
    logger.info("✓ spaCy loaded")
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("⚠️ spaCy not available")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("✓ sentence-transformers loaded")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers not available")

class TextProcessor:
    def __init__(self, spacy_model: str = "en_core_web_sm", embedding_model: str = "all-MiniLM-L6-v2"):
        self.nlp = None
        self.embedding_model = None
        
        # Load spaCy
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(spacy_model)
                logger.info(f"✓ spaCy model '{spacy_model}' loaded")
            except OSError:
                logger.warning(f"⚠️ spaCy model '{spacy_model}' not found, using basic tokenization")
        
        # Load embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info(f"✓ Embedding model '{embedding_model}' loaded")
            except Exception as e:
                logger.warning(f"⚠️ Could not load embedding model: {e}")
    
    def clean_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Clean and normalize text, detect/redact PII
        
        Returns:
            (cleaned_text, pii_flags)
        """
        pii_flags = []
        cleaned = text
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Detect and redact emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, cleaned):
            pii_flags.append('email')
            cleaned = re.sub(email_pattern, '[EMAIL_REDACTED]', cleaned)
        
        # Detect and redact phone numbers
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
            r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'    # (123) 456-7890
        ]
        for pattern in phone_patterns:
            if re.search(pattern, cleaned):
                pii_flags.append('phone')
                cleaned = re.sub(pattern, '[PHONE_REDACTED]', cleaned)
        
        # Detect SSN-like patterns
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, cleaned):
            pii_flags.append('ssn')
            cleaned = re.sub(ssn_pattern, '[SSN_REDACTED]', cleaned)
        
        # Detect credit cards
        cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        if re.search(cc_pattern, cleaned):
            pii_flags.append('credit_card')
            cleaned = re.sub(cc_pattern, '[CC_REDACTED]', cleaned)
        
        return cleaned, pii_flags
    
    def tokenize(self, text: str, lowercase: bool = False) -> List[str]:
        """
        Tokenize text using spaCy or fallback to basic tokenization
        
        Args:
            text: Input text
            lowercase: Whether to lowercase tokens
            
        Returns:
            List of tokens
        """
        if self.nlp is not None:
            # Use spaCy for advanced tokenization
            doc = self.nlp(text)
            tokens = [token.text for token in doc if not token.is_space]
        else:
            # Fallback to basic tokenization
            tokens = re.findall(r'\b\w+\b', text)
        
        if lowercase:
            tokens = [t.lower() for t in tokens]
        
        return tokens
    
    def segment_sentences(self, text: str) -> List[str]:
        """Segment text into sentences"""
        if self.nlp is not None:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Fallback to basic sentence splitting
            return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    
    def compute_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Compute sentence embedding
        
        Returns:
            Embedding vector or None if model not available
        """
        if self.embedding_model is None:
            return None
        
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"✗ Embedding computation error: {e}")
            return None
    
    async def process_text(
        self,
        original_text: str,
        compute_embedding: bool = False,
        lowercase_tokens: bool = False
    ) -> Dict:
        """
        Full text processing pipeline
        
        Returns:
            Dict with processing results
        """
        try:
            # 1. Clean text and detect PII
            cleaned_text, pii_flags = self.clean_text(original_text)
            
            # 2. Tokenize
            tokens = self.tokenize(cleaned_text, lowercase=lowercase_tokens)
            
            # 3. Segment sentences (for reference)
            sentences = self.segment_sentences(cleaned_text)
            
            # 4. Compute embedding if requested
            embedding = None
            embedding_dimensions = None
            if compute_embedding and self.embedding_model is not None:
                embedding = self.compute_embedding(cleaned_text)
                if embedding is not None:
                    embedding_dimensions = len(embedding)
            
            logger.info(f"✓ Text processed: {len(tokens)} tokens, {len(sentences)} sentences, PII: {pii_flags}")
            
            return {
                'cleaned_text': cleaned_text,
                'tokens': tokens,
                'token_count': len(tokens),
                'pii_redacted': len(pii_flags) > 0,
                'pii_flags': pii_flags,
                'embedding': embedding.tolist() if embedding is not None else None,
                'embedding_present': embedding is not None,
                'embedding_dimensions': embedding_dimensions,
                'sentence_count': len(sentences)
            }
            
        except Exception as e:
            logger.error(f"✗ Text processing error: {e}")
            raise

_text_processor = None

def get_text_processor(spacy_model: str = "en_core_web_sm", embedding_model: str = "all-MiniLM-L6-v2") -> TextProcessor:
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor(spacy_model, embedding_model)
    return _text_processor
