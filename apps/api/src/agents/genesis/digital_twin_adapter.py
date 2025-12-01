"""
Genesis Digital Twin Adapter - Integration Layer

This module provides the integration layer between the Genesis profiling
agents and the new Digital Twin system. It:

1. Intercepts trait detections from GenesisProfiler
2. Routes them to the Digital Twin via TwinAccessor
3. Syncs session state with Identity storage
4. Emits events for real-time UI updates

Architecture:
━━━━━━━━━━━━━

┌─────────────────┐       ┌──────────────────────┐       ┌─────────────────┐
│ GenesisProfiler │ ──▶   │ GenesisDigitalTwin   │ ──▶   │ DigitalTwinCore │
│ (trait detect)  │       │ Adapter              │       │ (persistence)   │
└─────────────────┘       └──────────────────────┘       └─────────────────┘
                                   │
                                   ▼
                          ┌──────────────────────┐
                          │ ProfileEventBus      │
                          │ (real-time events)   │
                          └──────────────────────┘

Usage:
    # In Genesis agents, instead of directly updating ProfileRubric:
    
    from .digital_twin_adapter import GenesisTwinAdapter
    
    adapter = await GenesisTwinAdapter.get_instance()
    
    # Record a detected trait
    await adapter.record_trait(
        trait_name="hd_type",
        value="projector",
        confidence=0.75,
        evidence=["mentioned waiting for invitations"],
        source="profiler"
    )
    
    # Get trait with full history
    trait = await adapter.get_trait("hd_type")
    
    # Sync session to identity
    await adapter.sync_session_to_identity(session_id, identity_id)

@module GenesisTwinAdapter
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import GenesisState

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


# =============================================================================
# TRAIT CATEGORIES (mirrors Genesis domain schemas)
# =============================================================================

class TraitCategory(str, Enum):
    """Categories of traits in the Genesis domain."""
    HUMAN_DESIGN = "human_design"
    JUNGIAN = "jungian"
    MBTI = "mbti"
    SOMATIC = "somatic"
    BEHAVIORAL = "behavioral"
    COGNITIVE = "cognitive"
    RELATIONAL = "relational"
    EMOTIONAL = "emotional"
    VALUES = "values"
    SHADOW = "shadow"
    CORE_PATTERNS = "core_patterns"


# Mapping from trait names to their categories
TRAIT_CATEGORY_MAP = {
    # Human Design
    "hd_type": TraitCategory.HUMAN_DESIGN,
    "hd_strategy": TraitCategory.HUMAN_DESIGN,
    "hd_authority": TraitCategory.HUMAN_DESIGN,
    "hd_profile": TraitCategory.HUMAN_DESIGN,
    "hd_definition": TraitCategory.HUMAN_DESIGN,
    "hd_not_self_theme": TraitCategory.HUMAN_DESIGN,
    "hd_signature": TraitCategory.HUMAN_DESIGN,
    "hd_centers": TraitCategory.HUMAN_DESIGN,
    "hd_channels": TraitCategory.HUMAN_DESIGN,
    "hd_gates": TraitCategory.HUMAN_DESIGN,
    
    # Jungian
    "jung_dominant": TraitCategory.JUNGIAN,
    "jung_auxiliary": TraitCategory.JUNGIAN,
    "jung_tertiary": TraitCategory.JUNGIAN,
    "jung_inferior": TraitCategory.JUNGIAN,
    "jung_shadow": TraitCategory.SHADOW,
    
    # MBTI
    "mbti_type": TraitCategory.MBTI,
    
    # Somatic
    "energy_pattern": TraitCategory.SOMATIC,
    "rest_pattern": TraitCategory.SOMATIC,
    "peak_hours": TraitCategory.SOMATIC,
    "nervous_system": TraitCategory.SOMATIC,
    
    # Behavioral
    "communication_style": TraitCategory.BEHAVIORAL,
    "learning_style": TraitCategory.BEHAVIORAL,
    "decision_pattern": TraitCategory.COGNITIVE,
    "conflict_style": TraitCategory.BEHAVIORAL,
    "social_style": TraitCategory.BEHAVIORAL,
    
    # Relational
    "relationship_pattern": TraitCategory.RELATIONAL,
    "attachment_style": TraitCategory.RELATIONAL,
    "love_language": TraitCategory.RELATIONAL,
    
    # Core Patterns
    "core_values": TraitCategory.VALUES,
    "core_fears": TraitCategory.SHADOW,
    "core_desires": TraitCategory.VALUES,
    "core_wound": TraitCategory.SHADOW,
    "core_gift": TraitCategory.CORE_PATTERNS,
    "life_themes": TraitCategory.CORE_PATTERNS,
    "growth_edges": TraitCategory.CORE_PATTERNS,
    "blind_spots": TraitCategory.SHADOW,
    "superpowers": TraitCategory.CORE_PATTERNS,
}


# =============================================================================
# TRAIT RESULT
# =============================================================================

@dataclass
class TraitResult:
    """Result of a trait query from Digital Twin."""
    path: str
    value: Any
    confidence: float
    source: str
    evidence: List[str]
    timestamp: datetime
    history: List[Dict[str, Any]]
    
    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.8
    
    @property
    def needs_probing(self) -> bool:
        return 0 < self.confidence < 0.8


# =============================================================================
# GENESIS DIGITAL TWIN ADAPTER
# =============================================================================

class GenesisTwinAdapter:
    """
    Adapter connecting Genesis agents to the Digital Twin system.
    
    This is the PRIMARY interface for Genesis agents to:
    - Record detected traits
    - Query existing traits
    - Sync session data
    - Emit real-time events
    
    All trait operations go through this adapter instead of
    directly updating ProfileRubric.
    """
    
    _instance: Optional["GenesisTwinAdapter"] = None
    _initialized: bool = False
    
    def __init__(self):
        self._digital_twin = None
        self._accessor = None
        self._event_bus = None
        self._current_identity_id: Optional[str] = None
    
    @classmethod
    async def get_instance(cls) -> "GenesisTwinAdapter":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        if not cls._instance._initialized:
            await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self) -> None:
        """Initialize connections to Digital Twin subsystem."""
        try:
            from ...digital_twin import (
                get_digital_twin_core,
                get_twin_accessor as get_accessor,
                get_event_bus,
            )
            
            self._digital_twin = await get_digital_twin_core()
            self._accessor = await get_accessor()
            self._event_bus = await get_event_bus()
            
            self._initialized = True
            logger.info("[GenesisTwinAdapter] Initialized successfully")
            
        except Exception as e:
            logger.error(f"[GenesisTwinAdapter] Initialization error: {e}")
            # Allow adapter to work without Digital Twin (graceful degradation)
            self._initialized = True
    
    # =========================================================================
    # IDENTITY MANAGEMENT
    # =========================================================================
    
    async def set_identity(self, identity_id: str) -> None:
        """
        Set the current identity for all operations.
        
        This should be called at the start of a session to bind
        all trait operations to a specific identity.
        """
        self._current_identity_id = identity_id
        
        if self._accessor:
            self._accessor.set_identity(identity_id)
        
        logger.info(f"[GenesisTwinAdapter] Set identity: {identity_id}")
    
    async def get_or_create_identity(
        self,
        session_id: Optional[str] = None
    ) -> str:
        """
        Get existing identity for session or create new one.
        
        Returns:
            Identity ID
        """
        if self._digital_twin:
            # Check if session has associated identity
            if session_id:
                identity = await self._digital_twin.get_identity_for_session(session_id)
                if identity:
                    await self.set_identity(identity.id)
                    return identity.id
            
            # Create new identity
            identity = await self._digital_twin.create_identity()
            await self.set_identity(identity.id)
            return identity.id
        
        # Fallback: use session_id as identity
        identity_id = session_id or f"identity_{datetime.now().timestamp()}"
        await self.set_identity(identity_id)
        return identity_id
    
    # =========================================================================
    # TRAIT OPERATIONS
    # =========================================================================
    
    async def record_trait(
        self,
        trait_name: str,
        value: Any,
        confidence: float = 0.5,
        evidence: Optional[List[str]] = None,
        source: str = "genesis",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a detected trait to the Digital Twin.
        
        This is the PRIMARY method for Genesis agents to record detections.
        
        Args:
            trait_name: Name of the trait (e.g., "hd_type", "jung_dominant")
            value: The detected value
            confidence: Confidence score 0-1
            evidence: List of supporting evidence strings
            source: Source of detection (e.g., "profiler", "hypothesis", "user")
            metadata: Additional metadata
            
        Returns:
            True if recorded successfully
        """
        # Build the trait path
        path = self._build_trait_path(trait_name)
        category = TRAIT_CATEGORY_MAP.get(trait_name, TraitCategory.CORE_PATTERNS)
        
        # Merge metadata
        full_metadata = {
            "trait_name": trait_name,
            "category": category.value,
            "evidence": evidence or [],
            "recorded_at": datetime.now().isoformat(),
        }
        if metadata:
            full_metadata.update(metadata)
        
        try:
            if self._digital_twin:
                # Write to Digital Twin
                await self._digital_twin.set(
                    path=path,
                    value=value,
                    confidence=confidence,
                    source=f"genesis.{source}",
                    metadata=full_metadata
                )
                
                # Emit event for real-time updates
                if self._event_bus:
                    await self._event_bus.emit(
                        event_type="trait_detected",
                        data={
                            "path": path,
                            "trait_name": trait_name,
                            "value": value,
                            "confidence": confidence,
                            "source": source,
                        }
                    )
                
                logger.debug(
                    f"[GenesisTwinAdapter] Recorded trait: {trait_name}={value} "
                    f"(confidence={confidence})"
                )
                return True
            else:
                # Fallback: log only
                logger.info(
                    f"[GenesisTwinAdapter] (no twin) Would record: {trait_name}={value}"
                )
                return False
                
        except Exception as e:
            logger.error(f"[GenesisTwinAdapter] Error recording trait: {e}")
            return False
    
    async def update_confidence(
        self,
        trait_name: str,
        confidence_delta: float,
        evidence: Optional[str] = None,
        source: str = "hypothesis"
    ) -> Optional[float]:
        """
        Update confidence for an existing trait.
        
        Args:
            trait_name: The trait to update
            confidence_delta: Amount to add/subtract (-1 to 1)
            evidence: New evidence to add
            source: Source of update
            
        Returns:
            New confidence value, or None if trait doesn't exist
        """
        path = self._build_trait_path(trait_name)
        
        try:
            if self._digital_twin:
                # Get current value
                current = await self._digital_twin.get(path)
                if current is None:
                    return None
                
                # Calculate new confidence
                old_confidence = current.get("confidence", 0.5) if isinstance(current, dict) else 0.5
                new_confidence = max(0.0, min(1.0, old_confidence + confidence_delta))
                
                # Update with new confidence
                current_value = current.get("value", current) if isinstance(current, dict) else current
                
                await self._digital_twin.set(
                    path=path,
                    value=current_value,
                    confidence=new_confidence,
                    source=f"genesis.{source}",
                    metadata={
                        "confidence_update": {
                            "from": old_confidence,
                            "to": new_confidence,
                            "delta": confidence_delta,
                            "evidence": evidence,
                        }
                    }
                )
                
                return new_confidence
            
            return None
            
        except Exception as e:
            logger.error(f"[GenesisTwinAdapter] Error updating confidence: {e}")
            return None
    
    async def get_trait(
        self,
        trait_name: str,
        include_history: bool = False
    ) -> Optional[TraitResult]:
        """
        Get a trait from the Digital Twin.
        
        Args:
            trait_name: The trait to get
            include_history: Whether to include change history
            
        Returns:
            TraitResult with full trait data, or None if not found
        """
        path = self._build_trait_path(trait_name)
        
        try:
            if self._accessor:
                result = await self._accessor.get(path)
                if result is None:
                    return None
                
                # Build TraitResult
                if isinstance(result, dict):
                    return TraitResult(
                        path=path,
                        value=result.get("value"),
                        confidence=result.get("confidence", 0.0),
                        source=result.get("source", "unknown"),
                        evidence=result.get("metadata", {}).get("evidence", []),
                        timestamp=datetime.fromisoformat(
                            result.get("timestamp", datetime.now().isoformat())
                        ),
                        history=result.get("history", []) if include_history else []
                    )
                else:
                    # Simple value
                    return TraitResult(
                        path=path,
                        value=result,
                        confidence=0.5,
                        source="unknown",
                        evidence=[],
                        timestamp=datetime.now(),
                        history=[]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"[GenesisTwinAdapter] Error getting trait: {e}")
            return None
    
    async def get_all_traits(
        self,
        category: Optional[TraitCategory] = None,
        min_confidence: float = 0.0
    ) -> List[TraitResult]:
        """
        Get all traits, optionally filtered.
        
        Args:
            category: Filter by category
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of TraitResult objects
        """
        results = []
        
        # Get all Genesis domain traits
        for trait_name, trait_category in TRAIT_CATEGORY_MAP.items():
            # Filter by category if specified
            if category and trait_category != category:
                continue
            
            trait = await self.get_trait(trait_name)
            if trait and trait.confidence >= min_confidence:
                results.append(trait)
        
        return results
    
    async def get_high_confidence_traits(
        self,
        threshold: float = 0.8
    ) -> List[TraitResult]:
        """Get all traits with high confidence."""
        return await self.get_all_traits(min_confidence=threshold)
    
    async def get_traits_needing_probing(
        self,
        threshold: float = 0.8
    ) -> List[TraitResult]:
        """Get traits that need more probing (low confidence but detected)."""
        all_traits = await self.get_all_traits(min_confidence=0.1)
        return [t for t in all_traits if t.confidence < threshold]
    
    # =========================================================================
    # SESSION SYNC
    # =========================================================================
    
    async def sync_session_state(
        self,
        session_id: str,
        state: "GenesisState"
    ) -> bool:
        """
        Sync Genesis session state to Digital Twin.
        
        This syncs the ProfileRubric data to the Digital Twin,
        enabling persistence across sessions.
        
        Args:
            session_id: The session ID
            state: The GenesisState to sync
            
        Returns:
            True if synced successfully
        """
        try:
            # Ensure we have an identity
            if not self._current_identity_id:
                await self.get_or_create_identity(session_id)
            
            # Sync rubric traits to Digital Twin
            rubric = state.rubric
            synced = 0
            
            for trait in rubric.get_all_traits():
                success = await self.record_trait(
                    trait_name=trait.name,
                    value=trait.value,
                    confidence=trait.confidence,
                    evidence=trait.evidence,
                    source="session_sync",
                    metadata={
                        "framework": trait.framework,
                        "category": trait.category,
                        "probed": trait.probed,
                    }
                )
                if success:
                    synced += 1
            
            # Store session metadata
            if self._digital_twin:
                await self._digital_twin.set(
                    path="genesis.session_meta",
                    value={
                        "session_id": session_id,
                        "phase": state.phase.value,
                        "question_index": state.question_index,
                        "total_questions": state.total_questions_asked,
                        "conversation_turn": state.conversation_turn,
                        "profile_complete": state.profile_complete,
                        "synced_at": datetime.now().isoformat(),
                    },
                    source="session_sync"
                )
            
            logger.info(
                f"[GenesisTwinAdapter] Synced session {session_id}: "
                f"{synced} traits"
            )
            return True
            
        except Exception as e:
            logger.error(f"[GenesisTwinAdapter] Session sync error: {e}")
            return False
    
    async def restore_session_from_twin(
        self,
        session_id: str,
        state: "GenesisState"
    ) -> bool:
        """
        Restore session state from Digital Twin.
        
        This populates the ProfileRubric from the Digital Twin,
        allowing session resumption.
        
        Args:
            session_id: The session ID
            state: The GenesisState to populate
            
        Returns:
            True if restored successfully
        """
        try:
            # Get all traits from twin
            all_traits = await self.get_all_traits()
            
            for trait_result in all_traits:
                # Create DetectedTrait and add to rubric
                from .state import DetectedTrait
                
                detected = DetectedTrait(
                    name=self._extract_trait_name(trait_result.path),
                    value=trait_result.value,
                    confidence=trait_result.confidence,
                    evidence=trait_result.evidence,
                    detected_at=trait_result.timestamp,
                )
                
                state.rubric.set_trait(detected.name, detected)
            
            # Restore session metadata
            if self._digital_twin:
                meta = await self._digital_twin.get("genesis.session_meta")
                if meta and isinstance(meta, dict):
                    from .state import GenesisPhase
                    state.phase = GenesisPhase(meta.get("phase", "awakening"))
                    state.question_index = meta.get("question_index", 0)
                    state.total_questions_asked = meta.get("total_questions", 0)
                    state.conversation_turn = meta.get("conversation_turn", 0)
                    state.profile_complete = meta.get("profile_complete", False)
            
            logger.info(
                f"[GenesisTwinAdapter] Restored session {session_id}: "
                f"{len(all_traits)} traits"
            )
            return True
            
        except Exception as e:
            logger.error(f"[GenesisTwinAdapter] Session restore error: {e}")
            return False
    
    # =========================================================================
    # COMPLETION & EXPORT
    # =========================================================================
    
    async def get_completion_percentage(self) -> float:
        """Calculate profile completion percentage."""
        core_traits = [
            "hd_type", "hd_strategy", "hd_authority",
            "jung_dominant", "energy_pattern",
            "core_wound", "core_gift", "decision_pattern"
        ]
        
        filled = 0
        for trait_name in core_traits:
            trait = await self.get_trait(trait_name)
            if trait and trait.confidence >= 0.7:
                filled += 1
        
        return (filled / len(core_traits)) * 100
    
    async def export_digital_twin(self) -> Dict[str, Any]:
        """
        Export the complete Digital Twin for this identity.
        
        Returns:
            Full Digital Twin data structure
        """
        if self._digital_twin and self._current_identity_id:
            return await self._digital_twin.export_identity(self._current_identity_id)
        
        # Fallback: export what we can get
        traits = await self.get_all_traits()
        return {
            "traits": {t.path: {"value": t.value, "confidence": t.confidence} for t in traits},
            "exported_at": datetime.now().isoformat(),
        }
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _build_trait_path(self, trait_name: str) -> str:
        """Build the full path for a trait."""
        return f"genesis.{trait_name}"
    
    def _extract_trait_name(self, path: str) -> str:
        """Extract trait name from path."""
        if path.startswith("genesis."):
            return path[8:]  # Remove "genesis." prefix
        return path


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_adapter_instance: Optional[GenesisTwinAdapter] = None


async def get_adapter() -> GenesisTwinAdapter:
    """Get the Genesis-Twin adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = await GenesisTwinAdapter.get_instance()
    return _adapter_instance


async def record_trait(
    trait_name: str,
    value: Any,
    confidence: float = 0.5,
    evidence: Optional[List[str]] = None,
    source: str = "genesis"
) -> bool:
    """Quick helper to record a trait."""
    adapter = await get_adapter()
    return await adapter.record_trait(
        trait_name=trait_name,
        value=value,
        confidence=confidence,
        evidence=evidence,
        source=source
    )


async def get_trait(trait_name: str) -> Optional[TraitResult]:
    """Quick helper to get a trait."""
    adapter = await get_adapter()
    return await adapter.get_trait(trait_name)
