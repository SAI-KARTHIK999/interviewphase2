"""
Answer Scorer Module
Implements NLP-based scoring for clarity, correctness, and relevance using transformer models.
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import logging
import time
import re

logger = logging.getLogger(__name__)


class AnswerScorer:
    """
    Scores interview answers on clarity, correctness, and relevance using transformer models.
    Supports both local RoBERTa/BERT models and optional cloud API inference.
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        use_cloud_api: bool = False,
        model_version: str = "v1.0",
        device: str = None
    ):
        """
        Initialize the answer scorer with specified models.
        
        Args:
            embedding_model: Sentence transformer model for embeddings
            use_cloud_api: Whether to use cloud API for inference
            model_version: Version identifier for models
            device: Device to run models on (cuda/cpu)
        """
        self.model_version = model_version
        self.use_cloud_api = use_cloud_api
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"Initializing AnswerScorer on device: {self.device}")
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(embedding_model, device=self.device)
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}. Using fallback.")
            self.embedding_model = None
        
        # Initialize component scoring models (lightweight sentiment models as proxies)
        # In production, these would be fine-tuned models
        try:
            self.clarity_scorer = self._init_clarity_scorer()
            self.correctness_scorer = self._init_correctness_scorer()
            self.relevance_scorer = self._init_relevance_scorer()
        except Exception as e:
            logger.warning(f"Failed to initialize scoring models: {e}")
            self.clarity_scorer = None
            self.correctness_scorer = None
            self.relevance_scorer = None
    
    def _init_clarity_scorer(self):
        """Initialize clarity scoring model (measures linguistic clarity)."""
        try:
            # Using a sentiment model as a proxy for clarity (positive = clear)
            # In production, replace with fine-tuned model
            return pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if self.device == "cuda" else -1,
                truncation=True
            )
        except:
            return None
    
    def _init_correctness_scorer(self):
        """Initialize correctness scoring model."""
        try:
            # Placeholder: would be replaced with fine-tuned correctness classifier
            return pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if self.device == "cuda" else -1,
                truncation=True
            )
        except:
            return None
    
    def _init_relevance_scorer(self):
        """Initialize relevance scoring model."""
        try:
            # Placeholder: would be replaced with fine-tuned relevance classifier
            return pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if self.device == "cuda" else -1,
                truncation=True
            )
        except:
            return None
    
    def compute_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Compute sentence embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.embedding_model or not text:
            return None
        
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            return None
    
    def score_clarity(self, text: str) -> Tuple[float, str]:
        """
        Score answer clarity (0-100).
        Measures: sentence structure, word choice, conciseness, hedge words.
        
        Args:
            text: Answer text
            
        Returns:
            (clarity_score, explanation)
        """
        if not text:
            return 0.0, "Empty answer"
        
        start_time = time.time()
        
        # Rule-based features
        hedge_words = ['maybe', 'perhaps', 'might', 'possibly', 'probably', 'kind of', 'sort of']
        filler_words = ['um', 'uh', 'like', 'you know', 'i mean']
        
        # Count features
        sentences = text.split('.')
        words = text.lower().split()
        hedge_count = sum(1 for word in words if word in hedge_words)
        filler_count = sum(1 for word in words if word in filler_words)
        avg_sentence_length = len(words) / max(len(sentences), 1)
        
        # Base score from rule-based features (0-100)
        clarity_score = 80.0
        
        # Penalties
        if hedge_count > 3:
            clarity_score -= min(hedge_count * 3, 20)
        if filler_count > 5:
            clarity_score -= min(filler_count * 2, 15)
        if avg_sentence_length > 30:
            clarity_score -= 10
        if avg_sentence_length < 5:
            clarity_score -= 5
        
        # Use ML model if available
        if self.clarity_scorer:
            try:
                result = self.clarity_scorer(text[:512])[0]  # Truncate for model
                # Positive sentiment correlates with clarity
                ml_score = result['score'] * 100 if result['label'] == 'POSITIVE' else (1 - result['score']) * 100
                # Blend rule-based and ML scores
                clarity_score = 0.6 * clarity_score + 0.4 * ml_score
            except Exception as e:
                logger.warning(f"ML clarity scoring failed: {e}")
        
        clarity_score = max(0, min(100, clarity_score))
        
        # Generate explanation
        explanation_parts = []
        if hedge_count <= 2:
            explanation_parts.append("minimal hedging")
        elif hedge_count > 3:
            explanation_parts.append(f"uses {hedge_count} hedge words")
        
        if filler_count == 0:
            explanation_parts.append("no filler words")
        elif filler_count > 5:
            explanation_parts.append(f"{filler_count} filler words detected")
        
        if 10 <= avg_sentence_length <= 20:
            explanation_parts.append("good sentence length")
        elif avg_sentence_length > 30:
            explanation_parts.append("overly long sentences")
        
        explanation = "Uses " + ", ".join(explanation_parts) if explanation_parts else "Standard clarity"
        
        latency = (time.time() - start_time) * 1000
        logger.debug(f"Clarity scoring took {latency:.2f}ms")
        
        return clarity_score, explanation
    
    def score_correctness(
        self,
        text: str,
        ground_truth: Optional[str] = None,
        question_embedding: Optional[np.ndarray] = None
    ) -> Tuple[float, str]:
        """
        Score answer correctness (0-100).
        Uses semantic similarity if ground truth available, otherwise uses ML classifier.
        
        Args:
            text: Answer text
            ground_truth: Expected answer (optional)
            question_embedding: Question embedding for relevance check
            
        Returns:
            (correctness_score, explanation)
        """
        if not text:
            return 0.0, "Empty answer"
        
        start_time = time.time()
        correctness_score = 50.0  # Default neutral score
        explanation = "No ground truth available"
        
        # If ground truth available, use semantic similarity
        if ground_truth and self.embedding_model:
            try:
                answer_emb = self.compute_embedding(text)
                truth_emb = self.compute_embedding(ground_truth)
                
                if answer_emb is not None and truth_emb is not None:
                    similarity = util.cos_sim(answer_emb, truth_emb).item()
                    # Map similarity [-1, 1] to score [0, 100]
                    similarity_score = ((similarity + 1) / 2) * 100
                    
                    # Use ML model for additional correctness signals
                    ml_score = 50.0
                    if self.correctness_scorer:
                        try:
                            result = self.correctness_scorer(text[:512])[0]
                            ml_score = result['score'] * 100 if result['label'] == 'POSITIVE' else (1 - result['score']) * 100
                        except Exception as e:
                            logger.warning(f"ML correctness scoring failed: {e}")
                    
                    # Weighted combination: 50% similarity, 50% ML
                    correctness_score = 0.5 * similarity_score + 0.5 * ml_score
                    
                    if similarity > 0.7:
                        explanation = "High semantic similarity to expected answer"
                    elif similarity > 0.4:
                        explanation = "Moderate similarity, some key concepts match"
                    else:
                        explanation = "Low similarity to expected answer"
            except Exception as e:
                logger.error(f"Semantic matching failed: {e}")
        
        # Fallback: use ML model only
        elif self.correctness_scorer:
            try:
                result = self.correctness_scorer(text[:512])[0]
                correctness_score = result['score'] * 100 if result['label'] == 'POSITIVE' else (1 - result['score']) * 100
                explanation = "Evaluated using ML classifier (no ground truth)"
            except Exception as e:
                logger.warning(f"ML correctness scoring failed: {e}")
                explanation = "Unable to evaluate correctness"
        
        # Check for factual indicators
        if re.search(r'\b(according to|research shows|studies indicate)\b', text.lower()):
            correctness_score += 5
            explanation += ", cites evidence"
        
        correctness_score = max(0, min(100, correctness_score))
        
        latency = (time.time() - start_time) * 1000
        logger.debug(f"Correctness scoring took {latency:.2f}ms")
        
        return correctness_score, explanation
    
    def score_relevance(
        self,
        answer_text: str,
        question_text: Optional[str] = None
    ) -> Tuple[float, str]:
        """
        Score answer relevance to the question (0-100).
        
        Args:
            answer_text: Answer text
            question_text: Question text (optional)
            
        Returns:
            (relevance_score, explanation)
        """
        if not answer_text:
            return 0.0, "Empty answer"
        
        start_time = time.time()
        relevance_score = 60.0  # Default neutral-positive score
        explanation = "General relevance assessment"
        
        # If question available, use semantic similarity
        if question_text and self.embedding_model:
            try:
                answer_emb = self.compute_embedding(answer_text)
                question_emb = self.compute_embedding(question_text)
                
                if answer_emb is not None and question_emb is not None:
                    similarity = util.cos_sim(answer_emb, question_emb).item()
                    # Map similarity to score, with higher baseline
                    similarity_score = ((similarity + 1) / 2) * 100
                    
                    # Relevance typically higher than raw similarity
                    relevance_score = min(100, similarity_score * 1.1)
                    
                    if similarity > 0.6:
                        explanation = "Highly relevant to question"
                    elif similarity > 0.3:
                        explanation = "Moderately relevant with some digression"
                    else:
                        explanation = "Low relevance to question"
            except Exception as e:
                logger.error(f"Relevance similarity failed: {e}")
        
        # Use ML model if available
        if self.relevance_scorer:
            try:
                result = self.relevance_scorer(answer_text[:512])[0]
                ml_score = result['score'] * 100 if result['label'] == 'POSITIVE' else (1 - result['score']) * 100
                
                # Blend with existing score if we have question similarity, otherwise use ML score
                if question_text and self.embedding_model:
                    relevance_score = 0.7 * relevance_score + 0.3 * ml_score
                else:
                    relevance_score = ml_score
                    explanation = "Evaluated using content analysis"
            except Exception as e:
                logger.warning(f"ML relevance scoring failed: {e}")
        
        relevance_score = max(0, min(100, relevance_score))
        
        latency = (time.time() - start_time) * 1000
        logger.debug(f"Relevance scoring took {latency:.2f}ms")
        
        return relevance_score, explanation
    
    def tokenize_text(self, text: str) -> Tuple[List[str], int]:
        """
        Tokenize text into words/tokens.
        
        Args:
            text: Input text
            
        Returns:
            (tokens_list, token_count)
        """
        if not text:
            return [], 0
        
        # Simple whitespace tokenization
        # For more sophisticated tokenization, use spaCy or transformers tokenizer
        tokens = text.split()
        
        # Clean tokens (remove punctuation from ends)
        import string
        cleaned_tokens = []
        for token in tokens:
            # Strip punctuation from start and end
            cleaned = token.strip(string.punctuation)
            if cleaned:  # Only add non-empty tokens
                cleaned_tokens.append(cleaned)
        
        return cleaned_tokens, len(cleaned_tokens)
    
    def analyze_answer(
        self,
        answer_text: str,
        question_text: Optional[str] = None,
        ground_truth: Optional[str] = None
    ) -> Dict:
        """
        Perform complete analysis of an answer.
        
        Args:
            answer_text: The candidate's answer
            question_text: The interview question
            ground_truth: Expected answer (if available)
            
        Returns:
            Dictionary with component scores and explanations
        """
        start_time = time.time()
        
        clarity_score, clarity_explanation = self.score_clarity(answer_text)
        correctness_score, correctness_explanation = self.score_correctness(
            answer_text, ground_truth
        )
        relevance_score, relevance_explanation = self.score_relevance(
            answer_text, question_text
        )
        
        # Compute embedding for storage/future use
        embedding = self.compute_embedding(answer_text)
        
        # Tokenize the text
        tokens, token_count = self.tokenize_text(answer_text)
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "clarity": clarity_score,
            "correctness": correctness_score,
            "relevance": relevance_score,
            "components": {
                "clarity_explanation": clarity_explanation,
                "correctness_explanation": correctness_explanation,
                "relevance_explanation": relevance_explanation
            },
            "embedding": embedding.tolist() if embedding is not None else None,
            "tokens": tokens,
            "token_count": token_count,
            "model_version": self.model_version,
            "processing_time_ms": processing_time
        }
