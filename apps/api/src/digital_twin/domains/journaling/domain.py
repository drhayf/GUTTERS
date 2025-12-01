"""
Journaling Domain - Main Domain Class

This module contains the main JournalingDomain class that orchestrates
all journaling functionality and integrates with the Digital Twin.

@module JournalingDomain
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, date
import logging

from ..base import BaseDomain, DomainSchema, TraitSchema
from ..registry import DomainRegistry
from ..core_types import (
    DomainType,
    DomainCapability,
    DomainMetadata,
    CoreDomainId,
)
from ...traits import TraitCategory, TraitFramework

from .schema import (
    JournalEntry,
    JournalingSchema,
    EntryType,
    MoodLevel,
    EmotionTag,
)

logger = logging.getLogger(__name__)


# =============================================================================
# JOURNALING CONFIG
# =============================================================================

@dataclass
class JournalingConfig:
    """
    Configuration for the Journaling domain.
    """
    # Feature toggles
    enable_emotion_detection: bool = True
    enable_theme_extraction: bool = True
    enable_sentiment_analysis: bool = True
    enable_prompt_personalization: bool = True
    
    # Analysis settings
    pattern_detection_days: int = 30
    min_entries_for_patterns: int = 5
    
    # Prompts
    daily_prompt_enabled: bool = True
    prompt_time: str = "09:00"
    
    # Privacy
    share_with_agents: bool = True
    anonymize_exports: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_emotion_detection": self.enable_emotion_detection,
            "enable_theme_extraction": self.enable_theme_extraction,
            "enable_sentiment_analysis": self.enable_sentiment_analysis,
            "enable_prompt_personalization": self.enable_prompt_personalization,
            "pattern_detection_days": self.pattern_detection_days,
            "min_entries_for_patterns": self.min_entries_for_patterns,
            "daily_prompt_enabled": self.daily_prompt_enabled,
            "prompt_time": self.prompt_time,
            "share_with_agents": self.share_with_agents,
            "anonymize_exports": self.anonymize_exports,
        }


# =============================================================================
# JOURNALING DOMAIN
# =============================================================================

@DomainRegistry.register
class JournalingDomain(BaseDomain):
    """
    Journaling Domain - Core Domain for self-reflection and insight capture.
    
    This is a CORE DOMAIN that provides:
    - Entry creation and management
    - Emotion detection and tracking
    - Theme and pattern analysis
    - Personalized prompt generation
    - Integration with Digital Twin traits
    """
    
    # -------------------------------------------------------------------------
    # Domain Identity
    # -------------------------------------------------------------------------
    
    domain_id = CoreDomainId.JOURNALING
    display_name = "Journaling"
    description = "Self-reflection, thought capture, and emotional processing"
    icon = "📔"
    version = "1.0.0"
    priority = 85  # High priority, core domain
    
    # Classification
    domain_type = DomainType.CORE
    is_core = True
    
    # Capabilities this domain provides
    capabilities = {
        DomainCapability.READ_TRAITS,
        DomainCapability.WRITE_TRAITS,
        DomainCapability.DETECT_PATTERNS,
        DomainCapability.GENERATE_INSIGHTS,
        DomainCapability.PROCESS_TEXT,
    }
    
    # Sub-domain IDs
    sub_domain_ids = [
        "prompts",      # AI-generated and curated prompts
        "reflections",  # Structured daily/weekly reflections
        "dreams",       # Dream journaling and analysis
        "gratitude",    # Gratitude practice tracking
    ]
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def __init__(self, config: Optional[JournalingConfig] = None):
        """Initialize the Journaling domain."""
        self.config = config or JournalingConfig()
        
        # In-memory caches (for scaffold - real impl uses persistence)
        self._entries: Dict[str, JournalEntry] = {}
        
        # Sub-module instances (lazy loaded)
        self._tracker = None
        self._analyzer = None
        self._prompt_system = None
        self._pattern_detector = None
        
        logger.info(f"JournalingDomain initialized with config: {self.config.to_dict()}")
    
    # -------------------------------------------------------------------------
    # Schema Implementation (Required by BaseDomain)
    # -------------------------------------------------------------------------
    
    def get_schema(self) -> DomainSchema:
        """Get the domain schema with all trait definitions."""
        schema = DomainSchema(domain_id=self.domain_id)
        
        for trait_key, trait_def in JournalingSchema.TRAITS.items():
            schema.add_trait(TraitSchema(
                name=trait_key,
                display_name=trait_def["name"],
                description=trait_def["description"],
                value_type=trait_def.get("value_type", "string"),
                category=TraitCategory.DETECTED,
                frameworks=[TraitFramework.BEHAVIORAL_PATTERNS],
            ))
        
        return schema
    
    # -------------------------------------------------------------------------
    # Entry Operations
    # -------------------------------------------------------------------------
    
    async def create_entry(
        self,
        content: str,
        entry_type: EntryType = EntryType.FREE_WRITE,
        mood_level: Optional[MoodLevel] = None,
        tags: Optional[List[str]] = None,
        prompt_id: Optional[str] = None,
        prompt_text: Optional[str] = None,
    ) -> JournalEntry:
        """Create a new journal entry."""
        entry = JournalEntry(
            entry_type=entry_type,
            content=content,
            word_count=len(content.split()),
            mood_level=mood_level,
            tags=tags or [],
            prompt_id=prompt_id,
            prompt_text=prompt_text,
        )
        
        self._entries[entry.entry_id] = entry
        
        # TODO: Trigger analysis pipeline
        # TODO: Update Digital Twin traits
        
        return entry
    
    async def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Retrieve a journal entry by ID."""
        return self._entries.get(entry_id)
    
    async def list_entries(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        entry_type: Optional[EntryType] = None,
        limit: int = 50,
    ) -> List[JournalEntry]:
        """List journal entries with optional filters."""
        entries = list(self._entries.values())
        
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        
        if start_date:
            entries = [e for e in entries if e.created_at.date() >= start_date]
        
        if end_date:
            entries = [e for e in entries if e.created_at.date() <= end_date]
        
        entries.sort(key=lambda e: e.created_at, reverse=True)
        
        return entries[:limit]
    
    # -------------------------------------------------------------------------
    # Domain Metadata
    # -------------------------------------------------------------------------
    
    @property
    def metadata(self) -> DomainMetadata:
        """Get domain metadata."""
        return DomainMetadata(
            domain_id=self.domain_id,
            display_name=self.display_name,
            description=self.description,
            domain_type=self.domain_type,
            icon=self.icon,
            version=self.version,
            priority=self.priority,
            capabilities=self.capabilities,
            sub_domain_ids=self.sub_domain_ids,
            is_core=self.is_core,
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_domain_instance: Optional[JournalingDomain] = None


def get_journaling_domain(config: Optional[JournalingConfig] = None) -> JournalingDomain:
    """Get or create the Journaling domain singleton."""
    global _domain_instance
    
    if _domain_instance is None:
        _domain_instance = JournalingDomain(config=config)
    
    return _domain_instance
