"""
Genesis Hypothesis Engine - The Logic Core

This module implements the "Hypothesis Engine" - the intelligent probing system
that maintains suspicions about user traits and generates targeted questions
to verify or refute them.

The Hypothesis Engine operates on a "Confidence Loop":
1. Receives hypotheses from the Profiler (e.g., "User might be a Projector")
2. Evaluates current confidence level
3. If confidence < 0.80, generates a probe to verify
4. Selects the optimal probe type (binary choice, slider, reflection, etc.)
5. Emits a QUESTION packet that the UI renders as an interactive component
6. Processes the user's response to update confidence

Key Constraints:
- Must NOT feel like an interrogation
- Probes should feel like natural conversational follow-ups
- The "Sovereign Guide" tone: wise, curious, compassionate
- Maximum 3 probes per hypothesis before forcing a decision

The Probe Types (mapped to Generative UI components):
- BINARY_CHOICE: "Which resonates more?" [A] vs [B]
- SLIDER: "On a scale of 1-10, how much..."
- CONFIRMATION: "It sounds like you... is that accurate?"
- REFLECTION: "Tell me more about how that feels..."
- CARD_SELECTION: Visual archetype cards for selection
"""

from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import logging
import random

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from .state import GenesisState, GenesisPhase, DetectedTrait
from ...shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    ProbeType,
    create_probe_packet,
    create_packet,
)
from ...core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# HYPOTHESIS MODEL
# =============================================================================

@dataclass
class Hypothesis:
    """
    A suspicion about a user trait that needs verification.
    
    The Hypothesis Engine maintains a pool of these and selects
    which ones to probe based on priority and confidence.
    """
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    trait_name: str = ""
    suspected_value: str = ""
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    probes_attempted: int = 0
    max_probes: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_probed: Optional[datetime] = None
    resolved: bool = False
    resolution_method: Optional[str] = None  # "confirmed", "refuted", "timeout"
    
    @property
    def needs_probing(self) -> bool:
        """Check if this hypothesis needs more verification."""
        if self.resolved:
            return False
        if self.confidence >= 0.80:
            return False
        if self.probes_attempted >= self.max_probes:
            return False
        return True
    
    @property
    def priority(self) -> float:
        """
        Calculate priority for probing.
        Higher = more important to probe.
        
        Factors:
        - Lower confidence = higher priority
        - More evidence = higher priority (we're close!)
        - Core traits (hd_type, jung_dominant) = higher priority
        """
        base_priority = 1.0 - self.confidence
        
        # Boost for near-confirmation
        if 0.6 <= self.confidence < 0.8:
            base_priority += 0.2
        
        # Boost for core traits
        core_traits = ["hd_type", "hd_strategy", "jung_dominant", "core_wound", "core_gift"]
        if self.trait_name in core_traits:
            base_priority += 0.3
        
        # Penalty for many failed probes
        if self.probes_attempted > 1:
            base_priority -= 0.1 * self.probes_attempted
        
        return max(0, min(1, base_priority))
    
    def add_evidence(self, evidence: str, boost: float = 0.1) -> None:
        """Add supporting evidence."""
        if evidence not in self.evidence:
            self.evidence.append(evidence)
            self.confidence = min(0.95, self.confidence + boost)
    
    def add_contradiction(self, evidence: str, penalty: float = 0.15) -> None:
        """Add contradicting evidence."""
        if evidence not in self.contradictions:
            self.contradictions.append(evidence)
            self.confidence = max(0.1, self.confidence - penalty)
    
    def mark_probed(self) -> None:
        """Record that a probe was attempted."""
        self.probes_attempted += 1
        self.last_probed = datetime.utcnow()
    
    def resolve(self, method: str) -> None:
        """Mark as resolved."""
        self.resolved = True
        self.resolution_method = method
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trait_name": self.trait_name,
            "suspected_value": self.suspected_value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "contradictions": self.contradictions,
            "probes_attempted": self.probes_attempted,
            "needs_probing": self.needs_probing,
            "priority": self.priority,
            "resolved": self.resolved,
        }


# =============================================================================
# PROBE TEMPLATES
# =============================================================================

PROBE_TEMPLATES = {
    "hd_type": {
        ProbeType.BINARY_CHOICE: [
            {
                "prompt": "When facing a new opportunity, what feels more natural?",
                "options": [
                    "I wait to feel a strong pull or response in my body",
                    "I sense when the timing is right and initiate action"
                ],
                "mappings": {
                    0: {"generator": 0.3, "manifesting_generator": 0.2},
                    1: {"manifestor": 0.3, "manifesting_generator": 0.15},
                }
            },
            {
                "prompt": "After a long day of working with others, you typically feel:",
                "options": [
                    "Energized if the work was satisfying, or frustrated if not",
                    "Depleted and needing significant alone time to recover"
                ],
                "mappings": {
                    0: {"generator": 0.25, "manifesting_generator": 0.25},
                    1: {"projector": 0.35, "reflector": 0.15},
                }
            },
        ],
        ProbeType.CONFIRMATION: [
            {
                "prompt": "It sounds like you often find yourself waiting for the right moment or invitation before taking action. Is that accurate?",
                "trait_if_yes": "projector",
                "confidence_boost": 0.25,
            },
            {
                "prompt": "You seem to have consistent, sustainable energy when you're doing work that lights you up. Does that resonate?",
                "trait_if_yes": "generator",
                "confidence_boost": 0.2,
            },
        ],
    },
    "jung_dominant": {
        ProbeType.BINARY_CHOICE: [
            {
                "prompt": "When solving a problem, you tend to:",
                "options": [
                    "Trust a gut feeling or sudden insight about the answer",
                    "Analyze the situation logically and systematically"
                ],
                "mappings": {
                    0: {"Ni": 0.2, "Ne": 0.15, "Fi": 0.1},
                    1: {"Ti": 0.25, "Te": 0.2},
                }
            },
            {
                "prompt": "In conversations, you're more drawn to:",
                "options": [
                    "Exploring possibilities and 'what ifs'",
                    "Discussing concrete experiences and practical matters"
                ],
                "mappings": {
                    0: {"Ne": 0.25, "Ni": 0.15},
                    1: {"Si": 0.25, "Se": 0.2},
                }
            },
        ],
    },
    "energy_pattern": {
        ProbeType.SLIDER: [
            {
                "prompt": "On a scale of 1-10, how consistent is your energy throughout the day? (1 = very variable, 10 = very stable)",
                "mappings": {
                    "low": {"wave": 0.3, "burst": 0.2},
                    "mid": {"sustainable": 0.1},
                    "high": {"sustainable": 0.3},
                }
            },
        ],
    },
    "core_wound": {
        ProbeType.REFLECTION: [
            {
                "prompt": "What's a recurring emotional pattern that has followed you through different life stages?",
            },
        ],
        ProbeType.CARD_SELECTION: [
            {
                "prompt": "Which of these core wounds resonates most deeply with your experience?",
                "options": [
                    "Abandonment - Fear of being left or forgotten",
                    "Unworthiness - Feeling not good enough",
                    "Invisibility - Feeling unseen or unheard",
                    "Powerlessness - Feeling unable to affect change",
                    "Betrayal - Difficulty trusting others"
                ],
            },
        ],
    },
}


# =============================================================================
# THE HYPOTHESIS ENGINE
# =============================================================================

class HypothesisEngine:
    """
    The Logic Core - maintains and probes hypotheses about the user.
    
    Usage:
        engine = HypothesisEngine()
        engine.add_hypothesis(trait="hd_type", value="projector", confidence=0.45, evidence=["tired"])
        probe = engine.generate_probe(state)
        engine.process_response(hypothesis_id, user_response)
    """
    
    def __init__(self):
        self.hypotheses: dict[str, Hypothesis] = {}
        self._llm = None
        self._setup_llm()
    
    def _setup_llm(self) -> None:
        """Initialize LLM for dynamic probe generation."""
        if not settings.GOOGLE_API_KEY:
            return
        
        try:
            self._llm = ChatGoogleGenerativeAI(
                model=settings.FAST_MODEL,
                temperature=0.7,
                google_api_key=settings.GOOGLE_API_KEY,
            )
        except Exception as e:
            logger.warning(f"[HypothesisEngine] LLM init error: {e}")
    
    def process_signal(self, signal) -> None:
        """
        Process a signal from the Profiler and create/update hypotheses.
        
        Signals contain suggested_traits which map to potential hypotheses.
        """
        if not signal:
            return
            
        suggested = getattr(signal, 'suggested_traits', None) or {}
        if not suggested:
            return
        
        # Each suggested trait becomes a hypothesis
        for trait_name, trait_info in suggested.items():
            if isinstance(trait_info, dict):
                value = trait_info.get('value', str(trait_info))
                confidence = trait_info.get('confidence', signal.confidence * 0.8)
            else:
                value = str(trait_info)
                confidence = signal.confidence * 0.8
            
            evidence = [f"Signal from {signal.source}: {signal.content[:100]}"]
            
            self.add_hypothesis(
                trait_name=trait_name,
                suspected_value=value,
                confidence=min(confidence, 0.7),  # Cap initial confidence
                evidence=evidence,
            )
    
    def add_hypothesis(
        self,
        trait_name: str,
        suspected_value: str,
        confidence: float,
        evidence: list[str],
    ) -> Hypothesis:
        """
        Add or update a hypothesis.
        
        If a hypothesis for this trait already exists, merge the evidence.
        """
        # Check for existing hypothesis on same trait
        for hyp in self.hypotheses.values():
            if hyp.trait_name == trait_name and hyp.suspected_value == suspected_value:
                # Merge evidence
                for ev in evidence:
                    hyp.add_evidence(ev, boost=0.05)
                return hyp
        
        # Create new hypothesis
        hyp = Hypothesis(
            trait_name=trait_name,
            suspected_value=suspected_value,
            confidence=confidence,
            evidence=evidence,
        )
        self.hypotheses[hyp.id] = hyp
        logger.info(f"[HypothesisEngine] Added hypothesis: {trait_name}={suspected_value} ({confidence:.0%})")
        return hyp
    
    def get_top_hypotheses(self, limit: int = 3) -> list[Hypothesis]:
        """Get the highest priority hypotheses that need probing."""
        probeable = [h for h in self.hypotheses.values() if h.needs_probing]
        probeable.sort(key=lambda h: h.priority, reverse=True)
        return probeable[:limit]
    
    def select_probe_type(self, hypothesis: Hypothesis, state: GenesisState) -> ProbeType:
        """
        Select the optimal probe type for a hypothesis.
        
        Considers:
        - What probe types have already been used
        - The phase (excavation prefers reflection, mapping prefers binary choice)
        - The trait type (core wounds prefer reflection/cards)
        """
        # Phase preferences
        phase_preferences = {
            GenesisPhase.AWAKENING: [ProbeType.REFLECTION, ProbeType.CONFIRMATION],
            GenesisPhase.EXCAVATION: [ProbeType.REFLECTION, ProbeType.CARD_SELECTION],
            GenesisPhase.MAPPING: [ProbeType.BINARY_CHOICE, ProbeType.SLIDER],
            GenesisPhase.SYNTHESIS: [ProbeType.CONFIRMATION, ProbeType.REFLECTION],
            GenesisPhase.ACTIVATION: [ProbeType.CONFIRMATION, ProbeType.BINARY_CHOICE],
        }
        
        # Trait preferences
        trait_preferences = {
            "hd_type": [ProbeType.BINARY_CHOICE, ProbeType.CONFIRMATION],
            "jung_dominant": [ProbeType.BINARY_CHOICE, ProbeType.SLIDER],
            "core_wound": [ProbeType.REFLECTION, ProbeType.CARD_SELECTION],
            "core_gift": [ProbeType.REFLECTION, ProbeType.CONFIRMATION],
            "energy_pattern": [ProbeType.SLIDER, ProbeType.BINARY_CHOICE],
        }
        
        # Get available templates for this trait
        templates = PROBE_TEMPLATES.get(hypothesis.trait_name, {})
        available_types = list(templates.keys())
        
        if not available_types:
            # Default fallback
            available_types = [ProbeType.CONFIRMATION, ProbeType.REFLECTION]
        
        # Combine preferences
        preferences = phase_preferences.get(state.phase, []) + trait_preferences.get(hypothesis.trait_name, [])
        
        # Select first matching preference
        for pref in preferences:
            if pref in available_types:
                return pref
        
        # Random from available
        return random.choice(available_types)
    
    def generate_probe(
        self, 
        state: GenesisState,
        hypothesis: Optional[Hypothesis] = None,
    ) -> Optional[SovereignPacket]:
        """
        Generate a probe packet for the highest priority hypothesis.
        
        Returns a QUESTION packet that the UI will render as an interactive component.
        """
        # Select hypothesis to probe
        if hypothesis is None:
            top_hypotheses = self.get_top_hypotheses(limit=1)
            if not top_hypotheses:
                return None
            hypothesis = top_hypotheses[0]
        
        # Select probe type
        probe_type = self.select_probe_type(hypothesis, state)
        
        # Get template
        templates = PROBE_TEMPLATES.get(hypothesis.trait_name, {})
        probe_templates = templates.get(probe_type, [])
        
        if probe_templates:
            template = random.choice(probe_templates)
            prompt = template.get("prompt", "Tell me more...")
            options = template.get("options")
        else:
            # Generate dynamic probe with LLM
            prompt, options = self._generate_dynamic_probe(hypothesis, probe_type, state)
        
        # Mark as probed
        hypothesis.mark_probed()
        
        # Create the packet
        packet = create_probe_packet(
            source_agent="genesis.hypothesis",
            probe_type=probe_type,
            prompt=prompt,
            options=options,
            resolves_trait=hypothesis.trait_name,
            expected_values={str(i): opt for i, opt in enumerate(options)} if options else None,
            session_id=state.session_id,
        )
        
        # Store the probe in pending
        state.add_pending_probe({
            "id": packet.packet_id,
            "hypothesis_id": hypothesis.id,
            "probe_type": probe_type.value,
            "trait_name": hypothesis.trait_name,
            "created_at": datetime.utcnow().isoformat(),
        })
        
        logger.info(f"[HypothesisEngine] Generated {probe_type.value} probe for {hypothesis.trait_name}")
        return packet
    
    def _generate_dynamic_probe(
        self,
        hypothesis: Hypothesis,
        probe_type: ProbeType,
        state: GenesisState,
    ) -> tuple[str, Optional[list[str]]]:
        """Generate a probe dynamically using LLM."""
        if not self._llm:
            return (f"Tell me more about your experience with {hypothesis.trait_name}...", None)
        
        try:
            prompt = f"""You are a wise guide helping someone understand themselves.

Current suspicion: {hypothesis.trait_name} might be "{hypothesis.suspected_value}"
Confidence: {hypothesis.confidence:.0%}
Evidence so far: {hypothesis.evidence}

Generate a {probe_type.value} probe that:
1. Feels like natural conversation, not interrogation
2. Helps verify or refute this suspicion
3. Uses warm, curious, compassionate language
4. Fits the {state.phase.value} phase of profiling

{"Generate two clear options for them to choose between." if probe_type == ProbeType.BINARY_CHOICE else ""}
{"Generate a reflective question that invites deep sharing." if probe_type == ProbeType.REFLECTION else ""}
{"Generate a yes/no confirmation of the suspected trait." if probe_type == ProbeType.CONFIRMATION else ""}

Respond with JSON:
{{"prompt": "...", "options": ["...", "..."] or null}}"""

            response = self._llm.invoke([
                SystemMessage(content="You are a compassionate profiler. Respond with valid JSON."),
                HumanMessage(content=prompt),
            ])
            
            import json
            data = json.loads(response.content)
            return (data.get("prompt", "Tell me more..."), data.get("options"))
            
        except Exception as e:
            logger.error(f"[HypothesisEngine] Dynamic probe generation failed: {e}")
            return (f"Tell me more about your experience with {hypothesis.trait_name}...", None)
    
    def process_response(
        self,
        hypothesis_id: str,
        response: str,
        selected_option: Optional[int] = None,
        slider_value: Optional[float] = None,
    ) -> Optional[Hypothesis]:
        """
        Process a user's response to a probe.
        
        Updates the hypothesis confidence based on the response.
        """
        hypothesis = self.hypotheses.get(hypothesis_id)
        if not hypothesis:
            logger.warning(f"[HypothesisEngine] Unknown hypothesis: {hypothesis_id}")
            return None
        
        # Get the template that was used (if any)
        templates = PROBE_TEMPLATES.get(hypothesis.trait_name, {})
        
        if selected_option is not None:
            # Binary choice or card selection
            for probe_type, probe_list in templates.items():
                if probe_type in [ProbeType.BINARY_CHOICE, ProbeType.CARD_SELECTION]:
                    for template in probe_list:
                        mappings = template.get("mappings", {})
                        if selected_option in mappings:
                            for trait_value, boost in mappings[selected_option].items():
                                if trait_value == hypothesis.suspected_value:
                                    hypothesis.add_evidence(f"Selected option {selected_option}", boost)
                                else:
                                    hypothesis.add_contradiction(f"Selected {trait_value} option", boost * 0.5)
                            break
        
        elif slider_value is not None:
            # Slider response
            if slider_value <= 3:
                category = "low"
            elif slider_value <= 7:
                category = "mid"
            else:
                category = "high"
            
            for probe_list in templates.get(ProbeType.SLIDER, []):
                mappings = probe_list.get("mappings", {})
                if category in mappings:
                    for trait_value, boost in mappings[category].items():
                        if trait_value == hypothesis.suspected_value:
                            hypothesis.add_evidence(f"Slider {slider_value}/10", boost)
        
        else:
            # Text response - use LLM to analyze
            if self._llm and response:
                self._analyze_text_response(hypothesis, response)
        
        # Check if resolved
        if hypothesis.confidence >= 0.80:
            hypothesis.resolve("confirmed")
            logger.info(f"[HypothesisEngine] Confirmed: {hypothesis.trait_name}={hypothesis.suspected_value}")
            # Write confirmed trait to Digital Twin
            self._write_confirmed_trait_to_twin(hypothesis)
        elif hypothesis.probes_attempted >= hypothesis.max_probes:
            hypothesis.resolve("timeout")
            logger.info(f"[HypothesisEngine] Timeout: {hypothesis.trait_name} (best guess: {hypothesis.suspected_value})")
            # Still write to Digital Twin with lower confidence
            self._write_confirmed_trait_to_twin(hypothesis)
        
        return hypothesis
    
    def _write_confirmed_trait_to_twin(self, hypothesis: Hypothesis) -> None:
        """
        Write a confirmed/resolved hypothesis to the Digital Twin.
        
        This is called when a hypothesis reaches high confidence or
        times out after max probes. The trait is persisted to the
        new identity-centric storage system.
        """
        try:
            import asyncio
            from .digital_twin_adapter import get_adapter
            
            async def _write():
                adapter = await get_adapter()
                await adapter.record_trait(
                    trait_name=hypothesis.trait_name,
                    value=hypothesis.suspected_value,
                    confidence=hypothesis.confidence,
                    evidence=hypothesis.evidence,
                    source=f"hypothesis.{hypothesis.resolution_method or 'resolved'}",
                    metadata={
                        "hypothesis_id": hypothesis.id,
                        "probes_attempted": hypothesis.probes_attempted,
                        "contradictions": hypothesis.contradictions,
                    }
                )
            
            # Run async in current event loop or create new one
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(_write())
            except RuntimeError:
                asyncio.run(_write())
                
        except Exception as e:
            # Graceful degradation - log but don't fail
            logger.debug(f"[HypothesisEngine] Digital Twin write skipped: {e}")
    
    def _analyze_text_response(self, hypothesis: Hypothesis, response: str) -> None:
        """Use LLM to analyze a text response for hypothesis verification."""
        if not self._llm:
            # Simple keyword matching fallback
            response_lower = response.lower()
            if hypothesis.suspected_value.lower() in response_lower:
                hypothesis.add_evidence(response[:100], boost=0.15)
            return
        
        try:
            prompt = f"""Analyze this response in the context of verifying a hypothesis.

Hypothesis: {hypothesis.trait_name} = "{hypothesis.suspected_value}"
Current confidence: {hypothesis.confidence:.0%}
Evidence so far: {hypothesis.evidence}

User's response: "{response}"

Does this response support or contradict the hypothesis?

Respond with JSON:
{{"verdict": "supports" | "contradicts" | "neutral", "strength": 0.0-0.3, "reason": "..."}}"""

            result = self._llm.invoke([
                SystemMessage(content="You are analyzing responses. Respond with valid JSON."),
                HumanMessage(content=prompt),
            ])
            
            import json
            data = json.loads(result.content)
            
            if data.get("verdict") == "supports":
                hypothesis.add_evidence(data.get("reason", response[:50]), data.get("strength", 0.1))
            elif data.get("verdict") == "contradicts":
                hypothesis.add_contradiction(data.get("reason", response[:50]), data.get("strength", 0.1))
            
        except Exception as e:
            logger.error(f"[HypothesisEngine] Text analysis failed: {e}")
    
    def get_priority_probe(self) -> Optional[Hypothesis]:
        """
        Get the highest priority hypothesis that needs probing.
        
        Returns the hypothesis with the highest priority score that
        still needs confirmation (confidence < 0.80 and not yet resolved).
        """
        top = self.get_top_hypotheses(limit=1)
        return top[0] if top else None
    
    def get_confirmed_hypotheses(self) -> list[Hypothesis]:
        """Get all hypotheses that have been confirmed (confidence >= 0.80 or resolved as confirmed)."""
        return [
            h for h in self.hypotheses.values()
            if h.confidence >= 0.80 or h.resolution_method == "confirmed"
        ]
    
    def get_summary(self) -> dict:
        """Get a summary of all hypotheses."""
        return {
            "total": len(self.hypotheses),
            "needs_probing": len([h for h in self.hypotheses.values() if h.needs_probing]),
            "confirmed": len([h for h in self.hypotheses.values() if h.resolution_method == "confirmed"]),
            "hypotheses": [h.to_dict() for h in self.hypotheses.values()],
        }
    
    def clear(self) -> None:
        """Clear all hypotheses."""
        self.hypotheses.clear()
