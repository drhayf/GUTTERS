"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        COUNCIL SERVICE - CORE                                ║
║                                                                              ║
║   Centralized service for Council of Systems integration.                    ║
║   Handles synthesis, events, notifications, and journal generation.          ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import structlog
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.events.bus import get_event_bus
from src.app.protocol.events import (
    MAGI_HEXAGRAM_CHANGE,
    MAGI_COUNCIL_SYNTHESIS,
    MAGI_RESONANCE_SHIFT,
)
from src.app.modules.intelligence.synthesis.harmonic import (
    CouncilOfSystems,
    IChingAdapter,
    CardologyAdapter,
    HarmonicSynthesis,
    ResonanceType,
    Element,
)
from src.app.modules.intelligence.iching import IChingKernel, GATE_DATABASE, DailyCode
from src.app.modules.intelligence.cardology import CardologyModule


logger = structlog.get_logger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class HexagramState(BaseModel):
    """Current I-Ching hexagram state for a user."""
    sun_gate: int
    sun_line: int
    sun_gate_name: str
    sun_gate_keynote: str
    sun_gene_key_gift: str
    sun_gene_key_shadow: str
    sun_gene_key_siddhi: str
    earth_gate: int
    earth_line: int
    earth_gate_name: str
    earth_gate_keynote: str
    earth_gene_key_gift: str
    polarity_theme: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def from_daily_code(cls, daily: DailyCode) -> "HexagramState":
        """Create from IChingKernel DailyCode."""
        sun = daily.sun_activation
        earth = daily.earth_activation
        sun_data = GATE_DATABASE.get(sun.gate)
        earth_data = GATE_DATABASE.get(earth.gate)
        
        return cls(
            sun_gate=sun.gate,
            sun_line=sun.line,
            sun_gate_name=sun_data.hd_name if sun_data else f"Gate {sun.gate}",
            sun_gate_keynote=sun_data.hd_keynote if sun_data else "",
            sun_gene_key_gift=sun_data.gk_gift if sun_data else "",
            sun_gene_key_shadow=sun_data.gk_shadow if sun_data else "",
            sun_gene_key_siddhi=sun_data.gk_siddhi if sun_data else "",
            earth_gate=earth.gate,
            earth_line=earth.line,
            earth_gate_name=earth_data.hd_name if earth_data else f"Gate {earth.gate}",
            earth_gate_keynote=earth_data.hd_keynote if earth_data else "",
            earth_gene_key_gift=earth_data.gk_gift if earth_data else "",
            polarity_theme=f"{sun_data.hd_keynote if sun_data else 'Unknown'} ↔ {earth_data.hd_keynote if earth_data else 'Unknown'}",
            timestamp=daily.timestamp,
        )


class CouncilSynthesisResult(BaseModel):
    """Full synthesis result from Council of Systems."""
    resonance_score: float
    resonance_type: str
    resonance_description: str
    element_profile: Dict[str, str]  # {system: element}
    unified_shadow: str
    unified_gift: str
    unified_siddhi: str
    macro_system: str
    macro_symbol: str
    macro_archetype: str
    macro_keynote: str
    micro_system: str
    micro_symbol: str
    micro_archetype: str
    micro_keynote: str
    quest_suggestions: list[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GateTransition(BaseModel):
    """Represents a gate transition event."""
    old_sun_gate: int
    new_sun_gate: int
    old_earth_gate: int
    new_earth_gate: int
    old_line: int
    new_line: int
    transition_type: str  # 'gate_shift' | 'line_shift'
    significance: str  # 'major' | 'minor'
    old_gate_data: Optional[Dict[str, Any]] = None
    new_gate_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# COUNCIL SERVICE
# =============================================================================

class CouncilService:
    """
    Centralized service for Council of Systems.
    
    Responsibilities:
    - Provide current hexagram and synthesis data
    - Detect gate transitions and emit events
    - Generate notifications for cosmic transitions
    - Track gate correlations for hypotheses
    - Coordinate with Observer for pattern detection
    """
    
    # Cache for last known state per user (in-memory for demo, use Redis in production)
    _user_states: Dict[int, HexagramState] = {}
    _user_resonance: Dict[int, str] = {}
    
    def __init__(self):
        """Initialize Council Service with kernels."""
        self._iching_kernel = IChingKernel()
        self._cardology_module = CardologyModule()
        self._council: Optional[CouncilOfSystems] = None
        
    def _get_council(self) -> CouncilOfSystems:
        """Lazy-initialize the Council of Systems."""
        if self._council is None:
            self._council = CouncilOfSystems()
            self._council.register_system(
                "I-Ching",
                IChingAdapter(self._iching_kernel),
                weight=1.0
            )
            self._council.register_system(
                "Cardology",
                CardologyAdapter(),
                weight=1.0
            )
        return self._council
    
    # =========================================================================
    # PUBLIC API: HEXAGRAM
    # =========================================================================
    
    def get_current_hexagram(self, dt: datetime = None) -> HexagramState:
        """
        Get current I-Ching hexagram (Sun/Earth gates).
        
        Args:
            dt: Datetime for calculation (default: now UTC)
            
        Returns:
            HexagramState with full gate data
        """
        if dt is None:
            dt = datetime.now(timezone.utc)
        
        daily = self._iching_kernel.get_daily_code(dt)
        return HexagramState.from_daily_code(daily)
    
    def get_hexagram_for_date(self, target_date: date) -> HexagramState:
        """
        Get hexagram for a specific date.
        
        Args:
            target_date: Date to calculate for
            
        Returns:
            HexagramState for that date
        """
        dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        return self.get_current_hexagram(dt)
    
    def get_gate_info(self, gate_number: int, line_number: int = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific gate and optionally a specific line.
        
        Args:
            gate_number: Gate 1-64
            line_number: Optional line 1-6
            
        Returns:
            Gate data including HD name, keynote, Gene Key frequencies, and line interpretation
        """
        gate_data = GATE_DATABASE.get(gate_number)
        if not gate_data:
            return None
        
        result = {
            "gate": gate_number,
            "iching_name": gate_data.iching_name,
            "hd_name": gate_data.hd_name,
            "hd_keynote": gate_data.hd_keynote,
            "hd_center": gate_data.hd_center,
            "upper_trigram": gate_data.upper_trigram,
            "lower_trigram": gate_data.lower_trigram,
            "gene_key_shadow": gate_data.gk_shadow,
            "gene_key_gift": gate_data.gk_gift,
            "gene_key_siddhi": gate_data.gk_siddhi,
            "codon_ring": gate_data.gk_codon_ring,
            "amino_acid": gate_data.gk_amino_acid,
            "harmonious_gates": gate_data.harmonious_gates or [],
            "challenging_gates": gate_data.challenging_gates or [],
            "keywords": gate_data.keywords or [],
        }
        
        # Add line interpretation if requested
        if line_number and gate_data.lines:
            line_data = gate_data.lines.get(line_number)
            if line_data:
                result["line"] = {
                    "number": line_data.number,
                    "name": line_data.name,
                    "keynote": line_data.keynote,
                    "description": line_data.description,
                    "exaltation": line_data.exaltation,
                    "detriment": line_data.detriment,
                }
        
        return result
    
    async def analyze_gate_history(
        self,
        user_id: int,
        gate_number: int,
        db_session: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Analyze user's historical experience during a specific gate.
        
        Examines journal entries, mood scores, and patterns from all times
        this gate has been active.
        
        Args:
            user_id: User ID
            gate_number: Gate 1-64
            db_session: Database session
            
        Returns:
            Historical analysis including mood averages, themes, occurrences
        """
        from datetime import timedelta
        from sqlalchemy import select, and_, func
        from src.app.models.journal_entry import JournalEntry
        
        if db_session is None:
            logger.warning("[CouncilService] analyze_gate_history called without db_session")
            return {
                "gate": gate_number,
                "error": "Database session required"
            }
        
        # Get gate data
        gate_data = GATE_DATABASE.get(gate_number)
        if not gate_data:
            return {"gate": gate_number, "error": "Invalid gate number"}
        
        # Calculate all dates when this gate was active
        # Each gate is active for approximately 5.625 days
        # We'll look back 2 years for meaningful patterns
        lookback_days = 730
        entries_during_gate = []
        
        # Get all journal entries for user
        query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.created_at >= datetime.now(timezone.utc) - timedelta(days=lookback_days)
            )
        ).order_by(JournalEntry.created_at)
        
        result = await db_session.execute(query)
        all_entries = result.scalars().all()
        
        # Filter entries that occurred during this gate
        for entry in all_entries:
            entry_hex = self.kernel.get_daily_code(entry.created_at)
            if entry_hex.sun_activation.gate == gate_number:
                entries_during_gate.append(entry)
        
        if not entries_during_gate:
            return {
                "gate": gate_number,
                "gate_name": gate_data.hd_name,
                "occurrences": 0,
                "message": "No journal entries during this gate in the past 2 years"
            }
        
        # Calculate statistics
        mood_scores = [e.mood for e in entries_during_gate if e.mood is not None]
        energy_scores = [e.energy for e in entries_during_gate if e.energy is not None]
        
        # Extract themes from content (simple keyword extraction)
        all_content = " ".join([e.content for e in entries_during_gate if e.content])
        # TODO: More sophisticated theme extraction with NLP
        
        # Calculate line distribution
        line_distribution = {}
        for entry in entries_during_gate:
            entry_hex = self.kernel.get_daily_code(entry.created_at)
            line = entry_hex.sun_activation.line
            line_distribution[line] = line_distribution.get(line, 0) + 1
        
        return {
            "gate": gate_number,
            "gate_name": gate_data.hd_name,
            "gene_key_gift": gate_data.gk_gift,
            "occurrences": len(entries_during_gate),
            "date_range": {
                "first": entries_during_gate[0].created_at.isoformat(),
                "last": entries_during_gate[-1].created_at.isoformat(),
            },
            "mood_analysis": {
                "average": sum(mood_scores) / len(mood_scores) if mood_scores else None,
                "min": min(mood_scores) if mood_scores else None,
                "max": max(mood_scores) if mood_scores else None,
                "count": len(mood_scores),
            },
            "energy_analysis": {
                "average": sum(energy_scores) / len(energy_scores) if energy_scores else None,
                "min": min(energy_scores) if energy_scores else None,
                "max": max(energy_scores) if energy_scores else None,
                "count": len(energy_scores),
            },
            "line_distribution": line_distribution,
            "keywords": gate_data.keywords or [],
            "sample_entries": [
                {
                    "date": e.created_at.isoformat(),
                    "mood": e.mood,
                    "energy": e.energy,
                    "preview": e.content[:200] if e.content else ""
                }
                for e in entries_during_gate[:5]  # First 5 entries
            ]
        }
    
    # =========================================================================
    # PUBLIC API: COUNCIL SYNTHESIS
    # =========================================================================
    
    def get_council_synthesis(
        self,
        birth_date: date = None,
        current_dt: datetime = None,
        user_id: int = None,
        db_session: AsyncSession = None
    ) -> CouncilSynthesisResult:
        """
        Get full Council of Systems synthesis.
        
        Args:
            birth_date: User's birth date (optional, for Cardology context)
            current_dt: Current datetime (default: now UTC)
            
        Returns:
            CouncilSynthesisResult with macro/micro synthesis
        """
        if current_dt is None:
            current_dt = datetime.now(timezone.utc)
        
        council = self._get_council()
        synthesis = council.synthesize(current_dt)
        
        # Extract macro (Cardology) and micro (I-Ching) readings
        macro = next((r for r in synthesis.systems if r.system_name == "Cardology"), None)
        micro = next((r for r in synthesis.systems if r.system_name == "I-Ching"), None)
        
        # Build element profile
        element_profile = {r.system_name: r.element.value for r in synthesis.systems}
        
        # Generate quest suggestions based on synthesis
        quest_suggestions = self._generate_quest_suggestions(synthesis)
        
        return CouncilSynthesisResult(
            resonance_score=synthesis.resonance_score,
            resonance_type=synthesis.resonance_type.value,
            resonance_description=synthesis.resonance_description,
            element_profile=element_profile,
            unified_shadow=synthesis.unified_shadow,
            unified_gift=synthesis.unified_gift,
            unified_siddhi=synthesis.unified_siddhi,
            macro_system=macro.system_name if macro else "Cardology",
            macro_symbol=macro.primary_symbol if macro else "",
            macro_archetype=macro.archetype if macro else "",
            macro_keynote=macro.keynote if macro else "",
            micro_system=micro.system_name if micro else "I-Ching",
            micro_symbol=micro.primary_symbol if micro else "",
            micro_archetype=micro.archetype if micro else "",
            micro_keynote=micro.keynote if micro else "",
            quest_suggestions=quest_suggestions,
            timestamp=current_dt,
        )
    
    def get_resonance_level(self) -> Tuple[float, str]:
        """Get current cross-system resonance level."""
        synthesis = self.get_council_synthesis()
        return synthesis.resonance_score, synthesis.resonance_type
    
    # =========================================================================
    # GATE TRANSITION DETECTION
    # =========================================================================
    
    async def check_gate_transition(
        self,
        user_id: int,
        current_dt: datetime = None
    ) -> Optional[GateTransition]:
        """
        Check if gate has transitioned since last check.
        
        Args:
            user_id: User ID
            current_dt: Current datetime
            
        Returns:
            GateTransition if transition detected, None otherwise
        """
        if current_dt is None:
            current_dt = datetime.now(timezone.utc)
        
        current_state = self.get_current_hexagram(current_dt)
        last_state = self._user_states.get(user_id)
        
        # No previous state - this is first check
        if last_state is None:
            self._user_states[user_id] = current_state
            return None
        
        # Check for gate shift (major transition)
        if current_state.sun_gate != last_state.sun_gate:
            transition = GateTransition(
                old_sun_gate=last_state.sun_gate,
                new_sun_gate=current_state.sun_gate,
                old_earth_gate=last_state.earth_gate,
                new_earth_gate=current_state.earth_gate,
                old_line=last_state.sun_line,
                new_line=current_state.sun_line,
                transition_type="gate_shift",
                significance="major",
                old_gate_data=self.get_gate_info(last_state.sun_gate),
                new_gate_data=self.get_gate_info(current_state.sun_gate),
                timestamp=current_dt,
            )
            self._user_states[user_id] = current_state
            return transition
        
        # Check for line shift (minor transition, ~daily)
        if current_state.sun_line != last_state.sun_line:
            transition = GateTransition(
                old_sun_gate=last_state.sun_gate,
                new_sun_gate=current_state.sun_gate,
                old_earth_gate=last_state.earth_gate,
                new_earth_gate=current_state.earth_gate,
                old_line=last_state.sun_line,
                new_line=current_state.sun_line,
                transition_type="line_shift",
                significance="minor",
                old_gate_data=self.get_gate_info(last_state.sun_gate),
                new_gate_data=self.get_gate_info(current_state.sun_gate),
                timestamp=current_dt,
            )
            self._user_states[user_id] = current_state
            return transition
        
        return None
    
    async def generate_context_aware_guidance(
        self,
        user_id: int,
        synthesis: CouncilSynthesisResult,
        db_session: AsyncSession
    ) -> list[str]:
        """
        Generate personalized guidance based on user's current context.
        
        Considers:
        - Recent journal sentiment
        - Active quests/goals
        - High-confidence hypotheses
        - Historical gate resonance
        - Current resonance type
        
        Args:
            user_id: User ID
            synthesis: Current synthesis
            db_session: Database session
            
        Returns:
            List of contextual guidance strings
        """
        from datetime import timedelta
        from sqlalchemy import select, and_, desc
        from src.app.models.journal_entry import JournalEntry
        from src.app.models.quest import Quest
        
        guidance = []
        
        # Get current hexagram
        hexagram = self.get_current_hexagram()
        gate_data = GATE_DATABASE.get(hexagram.sun_gate)
        
        # Get recent journal sentiment (last 7 days)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        recent_query = select(JournalEntry).where(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.created_at >= recent_cutoff
            )
        ).order_by(desc(JournalEntry.created_at)).limit(10)
        
        result = await db_session.execute(recent_query)
        recent_entries = result.scalars().all()
        
        recent_moods = [e.mood for e in recent_entries if e.mood is not None]
        avg_recent_mood = sum(recent_moods) / len(recent_moods) if recent_moods else 5.0
        
        # Get active quests
        quest_query = select(Quest).where(
            and_(
                Quest.user_id == user_id,
                Quest.status == "in_progress"
            )
        ).limit(5)
        
        result = await db_session.execute(quest_query)
        active_quests = result.scalars().all()
        
        # Get historical gate experience
        gate_history = await self.analyze_gate_history(user_id, hexagram.sun_gate, db_session)
        
        # Base guidance on gate energy
        base_guidance = f"Gate {hexagram.sun_gate} ({gate_data.hd_name}) invites you to explore {gate_data.gk_gift}"
        
        # ==== CONTEXT-AWARE ADAPTATIONS ====
        
        # 1. MOOD-BASED GUIDANCE
        if avg_recent_mood < 5 and synthesis.resonance_type in ["challenging", "dissonant"]:
            guidance.append(
                f"Your recent energy is low during this {synthesis.resonance_type} transit. "
                f"Extra self-care recommended. Focus on {gate_data.gk_gift} through gentle practices."
            )
        elif avg_recent_mood >= 7 and synthesis.resonance_type in ["harmonic", "supportive"]:
            guidance.append(
                f"You're riding high during this {synthesis.resonance_type} period! "
                f"Perfect time to express {gate_data.gk_gift} boldly. Take inspired action."
            )
        else:
            guidance.append(base_guidance)
        
        # 2. QUEST-ALIGNED GUIDANCE
        if active_quests:
            quest = active_quests[0]  # Focus on primary quest
            if synthesis.resonance_type in ["harmonic", "supportive"]:
                guidance.append(
                    f"Excellent cosmic alignment for working on '{quest.title}'. "
                    f"The energy of {gate_data.gk_gift} supports this endeavor."
                )
            elif synthesis.resonance_type == "challenging":
                guidance.append(
                    f"While working on '{quest.title}', be patient with yourself. "
                    f"Current energies may create resistance. Focus on small steps."
                )
        
        # 3. HISTORICAL PATTERN GUIDANCE
        if gate_history.get("occurrences", 0) > 0:
            hist_mood = gate_history["mood_analysis"].get("average")
            if hist_mood and hist_mood >= 7:
                guidance.append(
                    f"Historical insight: You've thrived during Gate {hexagram.sun_gate} "
                    f"({gate_history['occurrences']} times before, avg mood {hist_mood:.1f}). "
                    f"Trust your positive history with this energy."
                )
            elif hist_mood and hist_mood < 5:
                guidance.append(
                    f"Awareness: Gate {hexagram.sun_gate} has been challenging historically "
                    f"(avg mood {hist_mood:.1f} across {gate_history['occurrences']} transits). "
                    f"What strategies helped you last time?"
                )
        
        # 4. LINE-SPECIFIC GUIDANCE
        if gate_data.lines and hexagram.sun_line in gate_data.lines:
            line_data = gate_data.lines[hexagram.sun_line]
            guidance.append(
                f"Line {hexagram.sun_line} ({line_data.name}) emphasizes: {line_data.keynote}. "
                f"{line_data.description[:150]}..."
            )
        
        # 5. SHADOW-TO-GIFT TRANSFORMATION GUIDANCE
        if avg_recent_mood < 5:
            guidance.append(
                f"Transform {gate_data.gk_shadow} (shadow) into {gate_data.gk_gift} (gift). "
                f"Notice when {gate_data.gk_shadow} arises, breathe, and choose {gate_data.gk_gift}."
            )
        
        # 6. HARMONIOUS GATE ACTIVATION GUIDANCE
        if gate_data.harmonious_gates:
            guidance.append(
                f"Gates that harmonize with {hexagram.sun_gate}: {', '.join(map(str, gate_data.harmonious_gates[:3]))}. "
                f"If you have these in your chart, their energy amplifies now."
            )
        
        return guidance[:5]  # Return top 5 most relevant
    
    async def emit_gate_transition_event(
        self,
        user_id: int,
        transition: GateTransition
    ) -> None:
        """
        Emit MAGI_HEXAGRAM_CHANGE event for gate transition.
        Also emits MAGI_LINE_SHIFT for minor line transitions.
        
        Args:
            user_id: User ID
            transition: Gate transition data
        """
        bus = get_event_bus()
        
        # For major gate shifts, emit hexagram change
        if transition.transition_type == "gate_shift":
            payload = {
                "user_id": user_id,
                "old_sun_gate": transition.old_sun_gate,
                "new_sun_gate": transition.new_sun_gate,
                "old_earth_gate": transition.old_earth_gate,
                "new_earth_gate": transition.new_earth_gate,
                "sun_line": transition.new_line,
                "earth_line": transition.new_line,  # Assuming same line for polarity
                "transition_type": transition.transition_type,
                "significance": transition.significance,
                "new_gate_name": transition.new_gate_data.get("hd_name") if transition.new_gate_data else None,
                "new_gate_gift": transition.new_gate_data.get("gene_key_gift") if transition.new_gate_data else None,
                "timestamp": transition.timestamp.isoformat(),
            }
            
            await bus.publish("magi.hexagram.change", payload)
            
            logger.info(
                f"[CouncilService] Gate transition event emitted for user {user_id}: "
                f"Gate {transition.old_sun_gate} → Gate {transition.new_sun_gate}"
            )
        
        # For line shifts, emit line-specific event
        elif transition.transition_type == "line_shift":
            # Get line interpretation
            gate_info = self.get_gate_info(transition.new_sun_gate, transition.new_line)
            line_data = gate_info.get("line_interpretation", {})
            
            payload = {
                "user_id": user_id,
                "old_sun_gate": transition.old_sun_gate,
                "new_sun_gate": transition.new_sun_gate,
                "old_line": transition.old_line,
                "new_line": transition.new_line,
                "sun_line": transition.new_line,
                "line_name": line_data.get("name", "Unknown"),
                "line_keynote": line_data.get("keynote", ""),
                "line_description": line_data.get("description", ""),
                "timestamp": transition.timestamp.isoformat(),
            }
            
            await bus.publish("magi.line.shift", payload)
            
            logger.info(
                f"[CouncilService] Line shift event emitted for user {user_id}: "
                f"Gate {transition.new_sun_gate} Line {transition.old_line} → Line {transition.new_line}"
            )
    
    async def emit_synthesis_event(
        self,
        user_id: int,
        synthesis: CouncilSynthesisResult
    ) -> None:
        """
        Emit MAGI_COUNCIL_SYNTHESIS event.
        
        Args:
            user_id: User ID
            synthesis: Synthesis result
        """
        bus = get_event_bus()
        
        payload = {
            "user_id": user_id,
            "resonance_score": synthesis.resonance_score,
            "resonance_type": synthesis.resonance_type,
            "macro_theme": synthesis.macro_keynote,
            "micro_theme": synthesis.micro_keynote,
            "unified_gift": synthesis.unified_gift,
            "quest_suggestions": synthesis.quest_suggestions,
            "timestamp": synthesis.timestamp.isoformat(),
        }
        
        await bus.publish(MAGI_COUNCIL_SYNTHESIS, payload)
    
    async def check_resonance_shift(
        self,
        user_id: int,
        synthesis: CouncilSynthesisResult
    ) -> bool:
        """
        Check if resonance has shifted significantly.
        
        Args:
            user_id: User ID
            synthesis: Current synthesis
            
        Returns:
            True if resonance type changed
        """
        last_resonance = self._user_resonance.get(user_id)
        current_resonance = synthesis.resonance_type
        
        if last_resonance and last_resonance != current_resonance:
            bus = get_event_bus()
            
            payload = {
                "user_id": user_id,
                "old_resonance": last_resonance,
                "new_resonance": current_resonance,
                "elemental_profile": synthesis.element_profile,
            }
            
            await bus.publish(MAGI_RESONANCE_SHIFT, payload)
            self._user_resonance[user_id] = current_resonance
            
            logger.info(
                f"[CouncilService] Resonance shift for user {user_id}: "
                f"{last_resonance} → {current_resonance}"
            )
            return True
        
        self._user_resonance[user_id] = current_resonance
        return False
    
    # =========================================================================
    # MAGI CONTEXT FOR LLM
    # =========================================================================
    
    def get_magi_context(
        self,
        birth_date: date = None,
        current_dt: datetime = None
    ) -> Dict[str, Any]:
        """
        Get complete MAGI context for LLM injection.
        
        Used by query engine to provide cosmic awareness to the AI.
        
        Args:
            birth_date: User's birth date
            current_dt: Current datetime
            
        Returns:
            Dict with hexagram, cardology, and synthesis data
        """
        hexagram = self.get_current_hexagram(current_dt)
        synthesis = self.get_council_synthesis(birth_date, current_dt)
        
        return {
            "hexagram": {
                "sun_gate": hexagram.sun_gate,
                "sun_line": hexagram.sun_line,
                "sun_gate_name": hexagram.sun_gate_name,
                "sun_keynote": hexagram.sun_gate_keynote,
                "sun_gene_key_gift": hexagram.sun_gene_key_gift,
                "sun_gene_key_shadow": hexagram.sun_gene_key_shadow,
                "earth_gate": hexagram.earth_gate,
                "earth_line": hexagram.earth_line,
                "earth_gate_name": hexagram.earth_gate_name,
                "polarity_theme": hexagram.polarity_theme,
            },
            "council": {
                "resonance_score": synthesis.resonance_score,
                "resonance_type": synthesis.resonance_type,
                "macro_symbol": synthesis.macro_symbol,
                "macro_keynote": synthesis.macro_keynote,
                "micro_symbol": synthesis.micro_symbol,
                "micro_keynote": synthesis.micro_keynote,
                "unified_gift": synthesis.unified_gift,
                "unified_shadow": synthesis.unified_shadow,
            }
        }
    
    # =========================================================================
    # QUEST SUGGESTIONS
    # =========================================================================
    
    def _generate_quest_suggestions(
        self,
        synthesis: HarmonicSynthesis
    ) -> list[str]:
        """
        Generate quest suggestions based on current synthesis.
        
        Args:
            synthesis: Current harmonic synthesis
            
        Returns:
            List of quest suggestion strings
        """
        suggestions = []
        
        # Get readings
        macro = next((r for r in synthesis.systems if r.system_name == "Cardology"), None)
        micro = next((r for r in synthesis.systems if r.system_name == "I-Ching"), None)
        
        if micro:
            gift = micro.gift
            shadow = micro.shadow
            
            if gift:
                suggestions.append(f"Cultivate {gift}: Journal about moments when you embody this quality")
            if shadow:
                suggestions.append(f"Observe {shadow}: Notice without judgment when this pattern arises")
        
        if synthesis.resonance_type == ResonanceType.HARMONIC:
            suggestions.append("Flow state: Both systems align - ride this wave of synchronicity")
        elif synthesis.resonance_type == ResonanceType.CHALLENGING:
            suggestions.append("Integration work: Tension between cycles invites deeper growth")
        
        # Add universal quest
        suggestions.append("Reflective pause: 5 minutes of stillness to integrate today's cosmic weather")
        
        return suggestions[:3]  # Limit to 3 suggestions


# =============================================================================
# SINGLETON PATTERN
# =============================================================================

_council_service: Optional[CouncilService] = None


def get_council_service() -> CouncilService:
    """Get or create the Council Service singleton."""
    global _council_service
    if _council_service is None:
        _council_service = CouncilService()
    return _council_service
