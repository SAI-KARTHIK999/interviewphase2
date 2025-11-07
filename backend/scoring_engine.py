"""
Scoring Engine
Combines component scores into quality_score using configurable weights.
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Combines clarity, correctness, relevance, tone, and STT confidence scores
    into a weighted quality_score using configurable weights.
    """
    
    def __init__(self, config_path: str = "scoring_config.json"):
        """
        Initialize scoring engine with configuration.
        
        Args:
            config_path: Path to scoring configuration JSON file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.weights = self.config.get("weights", self._default_weights())
        
        # Validate weights sum to ~1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            logger.warning(
                f"Weights sum to {weight_sum:.3f}, not 1.0. "
                "Normalizing weights..."
            )
            self._normalize_weights()
    
    def _default_weights(self) -> Dict[str, float]:
        """Return default scoring weights."""
        return {
            "clarity": 0.30,
            "relevance": 0.30,
            "correctness": 0.25,
            "tone": 0.10,
            "stt_confidence": 0.05
        }
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded config from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file {self.config_path} not found. Using defaults.")
                return {"weights": self._default_weights()}
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
            return {"weights": self._default_weights()}
    
    def _normalize_weights(self):
        """Normalize weights to sum to 1.0."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
            logger.info(f"Normalized weights: {self.weights}")
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            self.config["weights"] = self.weights
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved config to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def update_weights(self, new_weights: Dict[str, float]):
        """
        Update scoring weights.
        
        Args:
            new_weights: Dictionary with new weight values
        """
        # Validate all required keys present
        required_keys = {"clarity", "relevance", "correctness", "tone", "stt_confidence"}
        if not required_keys.issubset(new_weights.keys()):
            raise ValueError(f"Missing required weight keys: {required_keys - set(new_weights.keys())}")
        
        # Validate values
        for key, value in new_weights.items():
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                raise ValueError(f"Invalid weight value for {key}: {value}. Must be 0-1.")
        
        self.weights = new_weights
        self._normalize_weights()
        logger.info(f"Updated weights: {self.weights}")
    
    def compute_quality_score(
        self,
        clarity: float,
        correctness: float,
        relevance: float,
        tone_score: float,
        stt_confidence: float
    ) -> float:
        """
        Compute weighted quality score from component scores.
        
        Args:
            clarity: Clarity score (0-100)
            correctness: Correctness score (0-100)
            relevance: Relevance score (0-100)
            tone_score: Tone score (0-100)
            stt_confidence: STT confidence (0-1, will be scaled to 0-100)
            
        Returns:
            Quality score (0-100)
        """
        # Normalize STT confidence to 0-100 scale
        stt_score = stt_confidence * 100
        
        # Compute weighted sum
        quality_score = (
            self.weights["clarity"] * clarity +
            self.weights["relevance"] * relevance +
            self.weights["correctness"] * correctness +
            self.weights["tone"] * tone_score +
            self.weights["stt_confidence"] * stt_score
        )
        
        # Ensure score is in valid range
        quality_score = max(0, min(100, quality_score))
        
        logger.debug(
            f"Quality score: {quality_score:.2f} = "
            f"{self.weights['clarity']:.2f}*{clarity:.1f} + "
            f"{self.weights['relevance']:.2f}*{relevance:.1f} + "
            f"{self.weights['correctness']:.2f}*{correctness:.1f} + "
            f"{self.weights['tone']:.2f}*{tone_score:.1f} + "
            f"{self.weights['stt_confidence']:.2f}*{stt_score:.1f}"
        )
        
        return quality_score
    
    def analyze_with_quality_score(
        self,
        clarity: float,
        correctness: float,
        relevance: float,
        tone_score: float,
        stt_confidence: float,
        components: Optional[Dict] = None
    ) -> Dict:
        """
        Compute quality score and return complete analysis.
        
        Args:
            clarity: Clarity score (0-100)
            correctness: Correctness score (0-100)
            relevance: Relevance score (0-100)
            tone_score: Tone score (0-100)
            stt_confidence: STT confidence (0-1)
            components: Optional component explanations
            
        Returns:
            Dictionary with quality_score and all components
        """
        quality_score = self.compute_quality_score(
            clarity, correctness, relevance, tone_score, stt_confidence
        )
        
        result = {
            "quality_score": round(quality_score, 1),
            "clarity": round(clarity, 1),
            "correctness": round(correctness, 1),
            "relevance": round(relevance, 1),
            "tone_score": round(tone_score, 1),
            "stt_confidence": round(stt_confidence, 2),
            "weights_used": self.weights.copy()
        }
        
        if components:
            result["components"] = components
        
        return result
    
    def get_weights(self) -> Dict[str, float]:
        """Get current scoring weights."""
        return self.weights.copy()
    
    def get_config(self) -> Dict:
        """Get full configuration."""
        return self.config.copy()
    
    def update_config(self, new_config: Dict):
        """
        Update full configuration.
        
        Args:
            new_config: New configuration dictionary
        """
        if "weights" in new_config:
            self.update_weights(new_config["weights"])
        
        # Update other config sections
        for key in ["models", "thresholds", "rate_limits", "retention", "semantic_matching"]:
            if key in new_config:
                self.config[key] = new_config[key]
        
        logger.info("Updated configuration")
