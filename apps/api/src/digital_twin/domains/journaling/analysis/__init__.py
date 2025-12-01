"""
Journaling Analysis - Emotion, Theme, and Sentiment Analysis

This sub-module provides content analysis capabilities:
- Emotion detection
- Theme extraction
- Sentiment analysis

@module JournalingAnalysis
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

from ..schema import JournalEntry, EmotionTag, EmotionCategory

logger = logging.getLogger(__name__)


# =============================================================================
# ANALYSIS RESULT
# =============================================================================

@dataclass
class AnalysisResult:
    """Result of analyzing a journal entry."""
    entry_id: str
    emotions: List[EmotionTag] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    word_count: int = 0
    analyzed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "emotions": [e.to_dict() for e in self.emotions],
            "themes": self.themes,
            "key_phrases": self.key_phrases,
            "sentiment_score": self.sentiment_score,
            "word_count": self.word_count,
            "analyzed_at": self.analyzed_at,
        }


# =============================================================================
# EMOTION ANALYZER
# =============================================================================

class EmotionAnalyzer:
    """
    Detects emotions in journal entries.
    
    SCAFFOLD: Basic keyword-based detection.
    Full implementation will use LLM for nuanced emotion detection.
    """
    
    # Simple emotion keyword mapping
    EMOTION_KEYWORDS = {
        EmotionCategory.JOY: ["happy", "joy", "excited", "grateful", "love", "wonderful"],
        EmotionCategory.SADNESS: ["sad", "depressed", "down", "unhappy", "grief", "loss"],
        EmotionCategory.ANGER: ["angry", "frustrated", "annoyed", "furious", "mad"],
        EmotionCategory.FEAR: ["afraid", "scared", "anxious", "worried", "nervous"],
        EmotionCategory.TRUST: ["trust", "believe", "confident", "secure", "faith"],
        EmotionCategory.SURPRISE: ["surprised", "shocked", "unexpected", "amazed"],
        EmotionCategory.DISGUST: ["disgusted", "gross", "revolting", "unpleasant"],
        EmotionCategory.ANTICIPATION: ["excited", "looking forward", "anticipate", "expect"],
    }
    
    async def analyze(self, entry: JournalEntry) -> List[EmotionTag]:
        """Detect emotions in an entry."""
        content_lower = entry.content.lower()
        detected = []
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in content_lower)
            if matches > 0:
                intensity = min(1.0, matches * 0.3)
                detected.append(EmotionTag(
                    category=emotion,
                    intensity=intensity,
                    confidence=0.6,  # Low confidence for keyword-based
                    source="ai_detected",
                ))
        
        return detected


# =============================================================================
# THEME EXTRACTOR
# =============================================================================

class ThemeExtractor:
    """
    Extracts themes from journal entries.
    
    SCAFFOLD: Basic keyword frequency.
    Full implementation will use LLM for semantic theme extraction.
    """
    
    async def extract(self, entry: JournalEntry) -> List[str]:
        """Extract themes from an entry."""
        # Scaffold: Return empty list
        # Full implementation will analyze content for themes
        return []
    
    async def extract_key_phrases(self, entry: JournalEntry) -> List[str]:
        """Extract key phrases from an entry."""
        # Scaffold: Return first few significant words
        words = entry.content.split()[:10]
        return [w for w in words if len(w) > 4]


# =============================================================================
# SENTIMENT ANALYZER
# =============================================================================

class SentimentAnalyzer:
    """
    Analyzes sentiment of journal entries.
    
    SCAFFOLD: Basic positive/negative word counting.
    Full implementation will use LLM for nuanced sentiment.
    """
    
    POSITIVE_WORDS = {"good", "great", "happy", "love", "wonderful", "excellent", "amazing"}
    NEGATIVE_WORDS = {"bad", "sad", "angry", "hate", "terrible", "awful", "horrible"}
    
    async def analyze(self, entry: JournalEntry) -> float:
        """
        Analyze sentiment of an entry.
        
        Returns: Score from -1.0 (negative) to 1.0 (positive)
        """
        words = set(entry.content.lower().split())
        
        pos_count = len(words & self.POSITIVE_WORDS)
        neg_count = len(words & self.NEGATIVE_WORDS)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total


__all__ = [
    "AnalysisResult",
    "EmotionAnalyzer",
    "ThemeExtractor",
    "SentimentAnalyzer",
]
