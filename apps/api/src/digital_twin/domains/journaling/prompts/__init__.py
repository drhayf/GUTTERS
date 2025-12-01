"""
Journaling Prompts - Prompt Generation and Library

This sub-module provides journaling prompts:
- AI-generated personalized prompts
- Curated prompt library
- Context-aware prompt selection

@module JournalingPrompts
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from uuid import uuid4
import random
import logging

from ..schema import EntryType

logger = logging.getLogger(__name__)


# =============================================================================
# PROMPT DATA STRUCTURES
# =============================================================================

@dataclass
class PersonalizedPrompt:
    """A personalized journaling prompt."""
    prompt_id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    entry_type: EntryType = EntryType.FREE_WRITE
    category: str = "general"
    personalization_score: float = 0.0  # How personalized (0-1)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "text": self.text,
            "entry_type": self.entry_type.value,
            "category": self.category,
            "personalization_score": self.personalization_score,
            "context": self.context,
        }


# =============================================================================
# PROMPT LIBRARY
# =============================================================================

class PromptLibrary:
    """
    Curated library of journaling prompts.
    
    Organized by category and entry type.
    """
    
    PROMPTS = {
        EntryType.FREE_WRITE: [
            "What's on your mind right now?",
            "Stream of consciousness: just write whatever comes to mind.",
            "If you could tell your past self one thing, what would it be?",
            "What's something you've been avoiding thinking about?",
        ],
        EntryType.GRATITUDE: [
            "What are three things you're grateful for today?",
            "Who made a positive difference in your life recently?",
            "What simple pleasure did you enjoy today?",
            "What challenge are you grateful for?",
        ],
        EntryType.REFLECTION: [
            "What was the highlight of your day and why?",
            "What did you learn about yourself today?",
            "If you could redo one thing from today, what would it be?",
            "What moment made you feel most alive today?",
        ],
        EntryType.EMOTIONAL: [
            "How are you feeling right now? Explore that emotion.",
            "What emotion have you been carrying with you lately?",
            "When did you last feel truly at peace?",
            "What's causing you stress right now?",
        ],
        EntryType.DREAM: [
            "Describe the dream you remember most vividly.",
            "What symbols appeared in your dream? What might they mean?",
            "How did your dream make you feel?",
            "Is there a recurring dream you've had?",
        ],
        EntryType.GOAL_CHECK: [
            "How are you progressing toward your current goals?",
            "What's one small step you can take toward your goal today?",
            "What obstacles are in your way? How can you overcome them?",
            "How do you feel about your progress?",
        ],
    }
    
    def get_prompt(self, entry_type: EntryType) -> str:
        """Get a random prompt for the given entry type."""
        prompts = self.PROMPTS.get(entry_type, self.PROMPTS[EntryType.FREE_WRITE])
        return random.choice(prompts)
    
    def get_all_prompts(self, entry_type: EntryType) -> List[str]:
        """Get all prompts for a given entry type."""
        return self.PROMPTS.get(entry_type, [])


# =============================================================================
# PROMPT GENERATOR
# =============================================================================

class PromptGenerator:
    """
    Generates personalized journaling prompts.
    
    SCAFFOLD: Uses library prompts.
    Full implementation will use LLM for personalization.
    """
    
    def __init__(self):
        self._library = PromptLibrary()
    
    async def generate(
        self,
        entry_type: Optional[EntryType] = None,
        context: Optional[Dict[str, Any]] = None,
        personalize: bool = True,
    ) -> PersonalizedPrompt:
        """Generate a prompt, optionally personalized."""
        
        etype = entry_type or EntryType.FREE_WRITE
        text = self._library.get_prompt(etype)
        
        return PersonalizedPrompt(
            text=text,
            entry_type=etype,
            category="library",
            personalization_score=0.0,  # Not personalized in scaffold
            context=context or {},
        )
    
    async def generate_multiple(
        self,
        count: int = 3,
        entry_type: Optional[EntryType] = None,
    ) -> List[PersonalizedPrompt]:
        """Generate multiple prompts."""
        prompts = []
        etype = entry_type or EntryType.FREE_WRITE
        all_texts = self._library.get_all_prompts(etype)
        
        for text in random.sample(all_texts, min(count, len(all_texts))):
            prompts.append(PersonalizedPrompt(
                text=text,
                entry_type=etype,
                category="library",
            ))
        
        return prompts


__all__ = [
    "PersonalizedPrompt",
    "PromptLibrary",
    "PromptGenerator",
]
