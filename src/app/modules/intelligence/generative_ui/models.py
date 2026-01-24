"""
Generative UI component models.

Defines specifications for interactive components that can be
streamed to the frontend during conversations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from datetime import datetime, timezone as dt_timezone
import uuid


class ComponentType(str, Enum):
    """Types of interactive components."""

    HYPOTHESIS_PROBE = "hypothesis_probe"
    MOOD_SLIDER = "mood_slider"
    ENERGY_SLIDER = "energy_slider"
    MULTI_SLIDER = "multi_slider"  # Added custom type for multi-slider support
    VOTE_COMPONENT = "vote_component"
    PATTERN_CONFIRMATION = "pattern_confirmation"
    SYMPTOM_CHECKLIST = "symptom_checklist"
    MULTIPLE_CHOICE = "multiple_choice"
    DATE_PICKER = "date_picker"
    TIME_RANGE = "time_range"


class SliderConfig(BaseModel):
    """Configuration for slider components."""

    id: str = Field(default="slider")
    label: Optional[str] = None
    min_value: int = Field(default=1)
    max_value: int = Field(default=10)
    initial_value: Optional[int] = None
    min_label: Optional[str] = None
    max_label: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)  # {1: "Low", 10: "High"}
    emoji_scale: Optional[Dict[int, str]] = None  # {1: "😌", 10: "😰"}


class VoteOption(BaseModel):
    """A single vote option."""

    id: str
    label: str
    description: Optional[str] = None
    emoji: Optional[str] = None


class ChecklistItem(BaseModel):
    """A checklist item."""

    id: str
    label: str
    description: Optional[str] = None
    category: Optional[str] = None


class MultipleChoiceOption(BaseModel):
    """A multiple choice option."""

    id: str
    text: str
    is_correct: Optional[bool] = None  # For knowledge checks


class HypothesisProbeSpec(BaseModel):
    """
    Specification for a hypothesis probe component.

    Used to gather data to test a hypothesis.

    Example:
        "I suspect you're sensitive to solar storms.
         Have you experienced these symptoms in the last 3 days?"
    """

    hypothesis_id: str
    hypothesis_text: str
    question: str
    items: List[ChecklistItem]
    allow_other: bool = False
    other_placeholder: Optional[str] = "Other symptoms..."


class MoodSliderSpec(BaseModel):
    """Mood rating slider (Single)."""

    question: str
    slider_config: SliderConfig
    context: Optional[str] = None  # "During the solar storm..."


class MultiSliderSpec(BaseModel):
    """Multiple sliders in one component (e.g. Mood, Energy, Anxiety)."""

    question: str
    sliders: List[SliderConfig]
    context: Optional[str] = None


class VoteComponentSpec(BaseModel):
    """Binary or multi-option vote."""

    question: str
    options: List[VoteOption]
    allow_multiple: bool = False


class PatternConfirmationSpec(BaseModel):
    """
    Confirm an Observer pattern.

    Example:
        "I've noticed you report headaches during solar storms.
         Does this feel accurate?"
    """

    pattern_id: str
    pattern_description: str
    confidence: float
    evidence: List[str]  # ["3 occurrences over 30 days", "0.82 correlation"]


class ComponentSpec(BaseModel):
    """
    Generic component specification.

    The AI generates this, and the frontend renders the appropriate
    React component based on component_type.
    """

    component_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    component_type: ComponentType

    # One of these will be populated based on type
    hypothesis_probe: Optional[HypothesisProbeSpec] = None
    mood_slider: Optional[MoodSliderSpec] = None
    multi_slider: Optional[MultiSliderSpec] = None
    vote: Optional[VoteComponentSpec] = None
    pattern_confirmation: Optional[PatternConfirmationSpec] = None

    # Metadata
    context_message: Optional[str] = None  # Message before component
    created_at: datetime = Field(default_factory=lambda: datetime.now(dt_timezone.utc))


class ComponentResponse(BaseModel):
    """
    User's response to an interactive component.

    Submitted from frontend when user completes interaction.
    """

    component_id: str
    component_type: ComponentType

    # Response data (varies by component type)
    slider_value: Optional[int] = None  # For single mood slider
    slider_values: Optional[Dict[str, int]] = None  # For multi-sliders {id: val}
    selected_ids: Optional[List[str]] = None  # For checklists, multiple choice
    vote_option_id: Optional[str] = None  # For votes
    confirmation: Optional[bool] = None  # For pattern confirmations
    text_input: Optional[str] = None  # For "other" fields

    # Metadata
    interaction_time_ms: Optional[int] = None  # How long user took
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(dt_timezone.utc))
