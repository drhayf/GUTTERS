"""
Journaling Schema - Data Types and Trait Definitions

This module defines all data structures and trait schemas for the
Journaling domain. These are the "nouns" of the journaling system.

Key Types:
- JournalEntry: A single journal entry with content and metadata
- EntryType: Classification of entry types (free write, prompted, etc.)
- EmotionTag: Detected or tagged emotions
- MoodLevel: Mood classification

Schema Design:
- All types are dataclasses with to_dict() for serialization
- Trait schemas define what the domain tracks
- Validation is built into the types

@module JournalingSchema
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


# =============================================================================
# ENUMS - Entry classification
# =============================================================================

class EntryType(str, Enum):
    """Types of journal entries."""
    FREE_WRITE = "free_write"          # Unstructured stream of consciousness
    PROMPTED = "prompted"               # Response to AI or system prompt
    GRATITUDE = "gratitude"             # Gratitude-focused entry
    REFLECTION = "reflection"           # Daily/weekly reflection
    DREAM = "dream"                     # Dream journaling
    GOAL_CHECK = "goal_check"           # Goal progress check-in
    EMOTIONAL = "emotional"             # Emotion-focused processing
    CREATIVE = "creative"               # Creative writing, poetry, etc.


class MoodLevel(str, Enum):
    """Mood classification for entries."""
    VERY_LOW = "very_low"
    LOW = "low"
    NEUTRAL = "neutral"
    GOOD = "good"
    EXCELLENT = "excellent"


class EmotionCategory(str, Enum):
    """Primary emotion categories (Plutchik's wheel simplified)."""
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"


# =============================================================================
# DATA CLASSES - Entry and emotion structures
# =============================================================================

@dataclass
class EmotionTag:
    """Detected or tagged emotion in an entry."""
    category: EmotionCategory
    intensity: float  # 0.0 - 1.0
    confidence: float  # AI detection confidence
    source: str = "user"  # "user", "ai_detected", "pattern_inferred"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "source": self.source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionTag":
        return cls(
            category=EmotionCategory(data["category"]),
            intensity=data.get("intensity", 0.5),
            confidence=data.get("confidence", 1.0),
            source=data.get("source", "user"),
        )


@dataclass
class JournalEntry:
    """A single journal entry."""
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    entry_type: EntryType = EntryType.FREE_WRITE
    content: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    
    # Mood and emotions
    mood_level: Optional[MoodLevel] = None
    emotions: List[EmotionTag] = field(default_factory=list)
    
    # Prompt (if prompted entry)
    prompt_id: Optional[str] = None
    prompt_text: Optional[str] = None
    
    # AI analysis results (populated after analysis)
    themes: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    
    # Linking
    linked_entry_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type.value,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "word_count": self.word_count,
            "mood_level": self.mood_level.value if self.mood_level else None,
            "emotions": [e.to_dict() for e in self.emotions],
            "prompt_id": self.prompt_id,
            "prompt_text": self.prompt_text,
            "themes": self.themes,
            "key_phrases": self.key_phrases,
            "sentiment_score": self.sentiment_score,
            "linked_entry_ids": self.linked_entry_ids,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JournalEntry":
        return cls(
            entry_id=data.get("entry_id", str(uuid4())),
            entry_type=EntryType(data.get("entry_type", "free_write")),
            content=data.get("content", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            word_count=data.get("word_count", 0),
            mood_level=MoodLevel(data["mood_level"]) if data.get("mood_level") else None,
            emotions=[EmotionTag.from_dict(e) for e in data.get("emotions", [])],
            prompt_id=data.get("prompt_id"),
            prompt_text=data.get("prompt_text"),
            themes=data.get("themes", []),
            key_phrases=data.get("key_phrases", []),
            sentiment_score=data.get("sentiment_score"),
            linked_entry_ids=data.get("linked_entry_ids", []),
            tags=data.get("tags", []),
        )


# =============================================================================
# JOURNALING SCHEMA - Master schema definition
# =============================================================================

class JournalingSchema:
    """
    Schema definitions for the Journaling domain.
    
    Provides trait schemas and validation rules.
    """
    
    # Trait schema definitions
    TRAITS = {
        # Writing patterns
        "preferred_entry_type": {
            "name": "Preferred Entry Type",
            "description": "User's most common/preferred journaling style",
            "value_type": "string",
            "possible_values": [e.value for e in EntryType],
        },
        "average_entry_length": {
            "name": "Average Entry Length",
            "description": "Typical word count per entry",
            "value_type": "integer",
            "unit": "words",
        },
        "journaling_frequency": {
            "name": "Journaling Frequency",
            "description": "How often user journals",
            "value_type": "string",
            "possible_values": ["daily", "several_times_week", "weekly", "occasionally", "rarely"],
        },
        "preferred_time_of_day": {
            "name": "Preferred Journaling Time",
            "description": "When user typically journals",
            "value_type": "string",
            "possible_values": ["morning", "midday", "evening", "night", "varies"],
        },
        
        # Emotional patterns
        "baseline_mood": {
            "name": "Baseline Mood",
            "description": "User's typical mood level in entries",
            "value_type": "string",
            "possible_values": [m.value for m in MoodLevel],
        },
        "dominant_emotions": {
            "name": "Dominant Emotions",
            "description": "Most frequently expressed emotion categories",
            "value_type": "list",
            "item_type": "string",
        },
        "emotional_range": {
            "name": "Emotional Range",
            "description": "Breadth of emotions expressed (1-10 scale)",
            "value_type": "float",
            "min_value": 1.0,
            "max_value": 10.0,
        },
        
        # Theme patterns
        "recurring_themes": {
            "name": "Recurring Themes",
            "description": "Themes that appear frequently across entries",
            "value_type": "list",
            "item_type": "string",
        },
        "growth_areas": {
            "name": "Growth Areas",
            "description": "Areas user is actively working on based on entries",
            "value_type": "list",
            "item_type": "string",
        },
        
        # Engagement patterns
        "prompt_responsiveness": {
            "name": "Prompt Responsiveness",
            "description": "How likely user is to respond to journaling prompts",
            "value_type": "float",
            "min_value": 0.0,
            "max_value": 1.0,
        },
        "reflection_depth": {
            "name": "Reflection Depth",
            "description": "How deeply user tends to reflect (surface to profound)",
            "value_type": "float",
            "min_value": 1.0,
            "max_value": 10.0,
        },
    }
    
    @classmethod
    def get_trait_schema(cls, trait_key: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific trait."""
        return cls.TRAITS.get(trait_key)
    
    @classmethod
    def list_traits(cls) -> List[str]:
        """List all trait keys."""
        return list(cls.TRAITS.keys())
    
    @classmethod
    def validate_entry(cls, entry: JournalEntry) -> List[str]:
        """Validate a journal entry. Returns list of validation errors."""
        errors = []
        
        if not entry.content:
            errors.append("Content cannot be empty")
        
        if entry.mood_level and entry.mood_level not in MoodLevel:
            errors.append(f"Invalid mood level: {entry.mood_level}")
        
        for emotion in entry.emotions:
            if emotion.intensity < 0 or emotion.intensity > 1:
                errors.append(f"Emotion intensity must be 0-1: {emotion.intensity}")
        
        return errors
