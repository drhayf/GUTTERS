"""
Genesis Profiler - The Silent Scout

This module implements the "Profiler" sub-agent - the silent observer that
analyzes user responses for archetypal patterns, energetic signatures, and
psychological indicators.

The Profiler operates in the background:
1. Receives each user response
2. Scans for pattern indicators using pre-defined signal maps
3. Updates the ProfileRubric with detected traits
4. Emits SovereignPackets for significant detections

Detection Frameworks:
- ENERGETIC (Human Design): Type indicators based on language patterns
- BIOLOGICAL (Somatic): Stress patterns, energy states
- PSYCHOLOGICAL (Jungian): Cognitive function indicators

The Profiler does NOT ask questions - it listens and detects.
It feeds the Hypothesis Engine with suspicions for verification.
"""

from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from .state import (
    GenesisState, 
    ProfileRubric, 
    DetectedTrait, 
    GenesisPhase
)
from ...shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    create_hypothesis_packet,
    create_insight_packet,
)
from ...core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# PATTERN SIGNAL MAPS
# =============================================================================

# Human Design Type Indicators
HD_TYPE_SIGNALS = {
    "generator": {
        "positive": [
            r"\b(respond|response|gut|sacral|energy|work|love\s+to|satisf|frustrat|wait\s+for)\b",
            r"\b(magnetic|attract|doing|building|sustainable)\b",
            r"\b(lit\s+up|excited|yes|uh-huh|sounds\s+good)\b",
        ],
        "negative": [
            r"\b(initiate|go\s+first|anger|impatient)\b",
        ],
    },
    "projector": {
        "positive": [
            r"\b(wait|invitation|recogni|bitter|guide|see|understand|penetrat)\b",
            r"\b(tired|rest|exhaust|energy\s+management|burnout)\b",
            r"\b(insight|wisdom|advise|observe|watch)\b",
            r"\b(need\s+to\s+be\s+seen|overlooked|invisible)\b",
        ],
        "negative": [
            r"\b(endless\s+energy|always\s+working|never\s+tired)\b",
        ],
    },
    "manifestor": {
        "positive": [
            r"\b(initiate|start|begin|create|anger|impact|inform)\b",
            r"\b(independent|alone|pioneer|trailblaz|first)\b",
            r"\b(powerful|force|push|make\s+it\s+happen)\b",
        ],
        "negative": [
            r"\b(wait|permission|need\s+approval)\b",
        ],
    },
    "reflector": {
        "positive": [
            r"\b(moon|lunar|cycle|28\s+days|mirror|reflect)\b",
            r"\b(disappoint|surprise|sample|taste|try)\b",
            r"\b(absorb|take\s+in|sense|environment)\b",
        ],
        "negative": [
            r"\b(consistent|same\s+every\s+day|predictable)\b",
        ],
    },
    "manifesting_generator": {
        "positive": [
            r"\b(multi-?passionate|many\s+interests|skip\s+steps|efficient)\b",
            r"\b(respond\s+and\s+initiate|fast|quick|shortcut)\b",
            r"\b(frustrat.*anger|pivot|change\s+direction)\b",
        ],
        "negative": [
            r"\b(one\s+thing|single\s+focus|linear)\b",
        ],
    },
}

# Jungian Cognitive Function Indicators
COGNITIVE_FUNCTION_SIGNALS = {
    "Ni": {  # Introverted Intuition
        "positive": [
            r"\b(vision|future|pattern|symbol|meaning|insight|know.*without|just\s+know)\b",
            r"\b(sense|hunch|intuit|foresee|predict|destiny)\b",
        ],
    },
    "Ne": {  # Extraverted Intuition
        "positive": [
            r"\b(possibilit|idea|connect|brainstorm|what\s+if|could\s+be|options)\b",
            r"\b(explore|curious|novel|new|innovative|creative)\b",
        ],
    },
    "Si": {  # Introverted Sensing
        "positive": [
            r"\b(remember|past|tradition|detail|concrete|familiar|routine)\b",
            r"\b(experience|history|precedent|how\s+it\s+was|used\s+to)\b",
        ],
    },
    "Se": {  # Extraverted Sensing
        "positive": [
            r"\b(present|moment|action|physical|sensory|experience|now)\b",
            r"\b(adventure|thrill|tangible|real|hands-?on)\b",
        ],
    },
    "Ti": {  # Introverted Thinking
        "positive": [
            r"\b(logic|analyze|system|framework|principle|understand\s+why)\b",
            r"\b(accurate|precise|categorize|define|model)\b",
        ],
    },
    "Te": {  # Extraverted Thinking
        "positive": [
            r"\b(efficient|organize|plan|goal|result|measure|productive)\b",
            r"\b(decide|implement|execute|structure|optimize)\b",
        ],
    },
    "Fi": {  # Introverted Feeling
        "positive": [
            r"\b(value|authentic|true\s+to|integrity|personal|individual)\b",
            r"\b(feel\s+right|inner\s+compass|moral|belief)\b",
        ],
    },
    "Fe": {  # Extraverted Feeling
        "positive": [
            r"\b(harmony|group|connect|empathy|people|relationship)\b",
            r"\b(care|nurture|support|community|together|we)\b",
        ],
    },
}

# Energy/Somatic Indicators
ENERGY_SIGNALS = {
    "sustainable": {
        "positive": [
            r"\b(steady|consistent|pace|marathon|endurance|reliable)\b",
        ],
    },
    "burst": {
        "positive": [
            r"\b(intense|short\s+burst|sprint|all-?in|then\s+crash|explosive)\b",
        ],
    },
    "wave": {
        "positive": [
            r"\b(cycle|wave|up\s+and\s+down|mood|emotional|ebb|flow)\b",
        ],
    },
    "depleted": {
        "positive": [
            r"\b(tired|exhaust|drain|burnout|empty|depleted|no\s+energy)\b",
        ],
    },
}


# =============================================================================
# SIGNAL DATACLASS (for internal use)
# =============================================================================

@dataclass
class Signal:
    """A detected signal from pattern analysis."""
    source: str = ""
    content: str = ""
    signal_type: str = ""
    confidence: float = 0.0
    suggested_traits: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "content": self.content,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "suggested_traits": self.suggested_traits,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# THE PROFILER
# =============================================================================

class GenesisProfiler:
    """
    The Silent Scout - analyzes responses for archetypal patterns.
    
    Usage:
        profiler = GenesisProfiler()
        # Sync version for simple use:
        signals = profiler.analyze_message(response, state)
        # Async version for full analysis:
        packets = await profiler.analyze(response, state)
    """
    
    def __init__(self):
        self._llm = None
        self._setup_llm()
    
    def _setup_llm(self) -> None:
        """Initialize the LLM for deep analysis."""
        if not settings.GOOGLE_API_KEY:
            return
        
        try:
            self._llm = ChatGoogleGenerativeAI(
                model=settings.FAST_MODEL,
                temperature=0.3,
                google_api_key=settings.GOOGLE_API_KEY,
            )
        except Exception as e:
            logger.warning(f"[Profiler] LLM init error: {e}")
    
    def analyze_message(
        self,
        response: str,
        state: GenesisState,
    ) -> list[Signal]:
        """
        Synchronous wrapper for pattern analysis.
        
        This is the simple API that returns Signal objects instead of packets.
        Used by the Core and Graph for quick pattern detection.
        
        Args:
            response: The user's response text
            state: Current genesis state
            
        Returns:
            List of Signal objects with detected patterns
        """
        signals = []
        response_lower = response.lower()
        
        # HD Type signals
        for hd_type, patterns in HD_TYPE_SIGNALS.items():
            for pattern in patterns.get("positive", []):
                if re.search(pattern, response_lower):
                    signals.append(Signal(
                        source="profiler.hd_type",
                        content=response[:100],
                        signal_type="pattern_match",
                        confidence=0.5,
                        suggested_traits={"hd_type": hd_type},
                    ))
                    break
        
        # Cognitive function signals
        for func, patterns in COGNITIVE_FUNCTION_SIGNALS.items():
            for pattern in patterns.get("positive", []):
                if re.search(pattern, response_lower):
                    signals.append(Signal(
                        source="profiler.cognitive",
                        content=response[:100],
                        signal_type="pattern_match",
                        confidence=0.45,
                        suggested_traits={"jung_dominant": func},
                    ))
                    break
        
        # Energy signals
        for energy_type, patterns in ENERGY_SIGNALS.items():
            for pattern in patterns.get("positive", []):
                if re.search(pattern, response_lower):
                    signals.append(Signal(
                        source="profiler.energy",
                        content=response[:100],
                        signal_type="pattern_match",
                        confidence=0.5,
                        suggested_traits={"energy_pattern": energy_type},
                    ))
                    break
        
        logger.info(f"[Profiler] analyze_message detected {len(signals)} signals")
        return signals
    
    async def analyze(
        self, 
        response: str, 
        state: GenesisState,
        context: Optional[str] = None,
    ) -> list[SovereignPacket]:
        """
        Analyze a user response for patterns and traits.
        
        Args:
            response: The user's response text
            state: Current genesis state
            context: Additional context (e.g., the question asked)
            
        Returns:
            List of SovereignPackets with detected patterns and hypotheses
        """
        packets = []
        
        # 1. Pattern matching (fast, rule-based) - now async for Digital Twin writes
        pattern_packets = await self._scan_patterns_async(response, state)
        packets.extend(pattern_packets)
        
        # 2. LLM-based deep analysis (slower, more nuanced)
        if self._llm and len(response) > 50:
            llm_packets = await self._deep_analyze(response, state, context)
            packets.extend(llm_packets)
        
        logger.info(f"[Profiler] Detected {len(packets)} patterns in response")
        return packets
    
    async def _write_to_digital_twin(
        self,
        trait_name: str,
        value: str,
        confidence: float,
        evidence: list,
        source: str
    ) -> None:
        """
        Write detected trait to Digital Twin system.
        
        This ensures all trait detections are persisted to the
        new identity-centric storage system.
        """
        try:
            from .digital_twin_adapter import get_adapter
            adapter = await get_adapter()
            await adapter.record_trait(
                trait_name=trait_name,
                value=value,
                confidence=confidence,
                evidence=evidence,
                source=source
            )
        except Exception as e:
            # Graceful degradation - log but don't fail the profiling
            logger.debug(f"[Profiler] Digital Twin write skipped: {e}")
    
    async def _scan_patterns_async(
        self, 
        response: str, 
        state: GenesisState
    ) -> list[SovereignPacket]:
        """
        Fast pattern matching using regex with Digital Twin integration.
        
        This is the async version that also writes to Digital Twin.
        """
        packets = []
        response_lower = response.lower()
        
        # Scan for Human Design Type indicators
        type_scores = {}
        for hd_type, signals in HD_TYPE_SIGNALS.items():
            score = 0
            evidence = []
            
            for pattern in signals.get("positive", []):
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                if matches:
                    score += len(matches) * 0.15
                    evidence.extend(matches[:2])
            
            for pattern in signals.get("negative", []):
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                if matches:
                    score -= len(matches) * 0.1
            
            if score > 0.1:
                type_scores[hd_type] = {"score": min(score, 0.7), "evidence": evidence}
        
        # Emit hypothesis for strongest HD type signal
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1]["score"])
            if best_type[1]["score"] >= 0.2:
                packet = create_hypothesis_packet(
                    source_agent="genesis.profiler",
                    trait_name="hd_type",
                    suspected_value=best_type[0],
                    confidence=best_type[1]["score"],
                    evidence=best_type[1]["evidence"],
                    session_id=state.session_id,
                )
                packets.append(packet)
                
                # Update rubric (legacy - kept for backward compatibility)
                existing = state.rubric.hd_type
                if existing:
                    if existing.value == best_type[0]:
                        existing.add_evidence(response[:100], best_type[1]["score"] * 0.3)
                    else:
                        # Competing hypothesis
                        existing.add_contradiction(f"Also detected: {best_type[0]}")
                else:
                    state.rubric.hd_type = DetectedTrait(
                        name="hd_type",
                        value=best_type[0],
                        confidence=best_type[1]["score"],
                        evidence=best_type[1]["evidence"],
                        framework="human_design",
                        category="type",
                    )
                
                # ALSO write to Digital Twin (new system)
                await self._write_to_digital_twin(
                    trait_name="hd_type",
                    value=best_type[0],
                    confidence=best_type[1]["score"],
                    evidence=best_type[1]["evidence"],
                    source="profiler.pattern_match"
                )
        
        # Scan for Cognitive Function indicators
        function_scores = {}
        for func, signals in COGNITIVE_FUNCTION_SIGNALS.items():
            score = 0
            evidence = []
            
            for pattern in signals.get("positive", []):
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                if matches:
                    score += len(matches) * 0.12
                    evidence.extend(matches[:2])
            
            if score > 0.1:
                function_scores[func] = {"score": min(score, 0.6), "evidence": evidence}
        
        # Emit top cognitive function detection
        if function_scores:
            best_func = max(function_scores.items(), key=lambda x: x[1]["score"])
            if best_func[1]["score"] >= 0.15:
                packet = create_hypothesis_packet(
                    source_agent="genesis.profiler",
                    trait_name="jung_dominant",
                    suspected_value=best_func[0],
                    confidence=best_func[1]["score"],
                    evidence=best_func[1]["evidence"],
                    session_id=state.session_id,
                )
                packets.append(packet)
                
                # Write to Digital Twin
                await self._write_to_digital_twin(
                    trait_name="jung_dominant",
                    value=best_func[0],
                    confidence=best_func[1]["score"],
                    evidence=best_func[1]["evidence"],
                    source="profiler.pattern_match"
                )
        
        # Scan for Energy patterns
        for energy_type, signals in ENERGY_SIGNALS.items():
            for pattern in signals.get("positive", []):
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                if matches:
                    packet = create_insight_packet(
                        source_agent="genesis.profiler",
                        pattern_name=f"energy_{energy_type}",
                        pattern_category="somatic",
                        indicators=matches[:3],
                        strength=min(len(matches) * 0.2, 0.6),
                        framework="somatic",
                        session_id=state.session_id,
                    )
                    packets.append(packet)
                    
                    # Write to Digital Twin
                    await self._write_to_digital_twin(
                        trait_name="energy_pattern",
                        value=energy_type,
                        confidence=min(len(matches) * 0.2, 0.6),
                        evidence=matches[:3],
                        source="profiler.pattern_match"
                    )
                    break  # One energy pattern per response
        
        return packets
    
    def _scan_patterns(
        self, 
        response: str, 
        state: GenesisState
    ) -> list[SovereignPacket]:
        """
        Legacy sync version of pattern matching.
        
        Kept for backward compatibility. Use _scan_patterns_async for
        full Digital Twin integration.
        """
        # Run synchronously - just call the pattern matching logic
        # without Digital Twin writes
        packets = []
        response_lower = response.lower()
        
        # Simplified version without Digital Twin writes
        type_scores = {}
        for hd_type, signals in HD_TYPE_SIGNALS.items():
            score = 0
            evidence = []
            for pattern in signals.get("positive", []):
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                if matches:
                    score += len(matches) * 0.15
                    evidence.extend(matches[:2])
            if score > 0.1:
                type_scores[hd_type] = {"score": min(score, 0.7), "evidence": evidence}
        
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1]["score"])
            if best_type[1]["score"] >= 0.2:
                packet = create_hypothesis_packet(
                    source_agent="genesis.profiler",
                    trait_name="hd_type",
                    suspected_value=best_type[0],
                    confidence=best_type[1]["score"],
                    evidence=best_type[1]["evidence"],
                    session_id=state.session_id,
                )
                packets.append(packet)
        
        return packets
    
    async def _deep_analyze(
        self, 
        response: str, 
        state: GenesisState,
        context: Optional[str] = None,
    ) -> list[SovereignPacket]:
        """LLM-based deep analysis for nuanced pattern detection."""
        packets = []
        
        if not self._llm:
            return packets
        
        try:
            # Build context from previous responses
            history = "\n".join([
                f"Q: {r.get('question', '')[:80]}... A: {r.get('response', '')[:80]}..."
                for r in state.responses[-3:]
            ])
            
            prompt = f"""You are a master profiler analyzing someone's psyche through their words.

Current Phase: {state.phase.value.upper()}
Previous Context:
{history}

Latest Response: "{response}"

Analyze this response for:
1. ENERGETIC TYPE (Human Design): Generator, Projector, Manifestor, Reflector, or Manifesting Generator
2. COGNITIVE PATTERN (Jung): Which cognitive function is most evident? (Ni, Ne, Si, Se, Ti, Te, Fi, Fe)
3. SHADOW PATTERN: What might this person be avoiding or suppressing?
4. CORE GIFT: What natural strength is emerging?

Respond in JSON format:
{{
    "energetic_type": {{"value": "...", "confidence": 0.0-1.0, "evidence": "..."}},
    "cognitive_function": {{"value": "...", "confidence": 0.0-1.0, "evidence": "..."}},
    "shadow_pattern": {{"value": "...", "confidence": 0.0-1.0, "evidence": "..."}},
    "core_gift": {{"value": "...", "confidence": 0.0-1.0, "evidence": "..."}}
}}

Only include patterns you detect with confidence > 0.3."""

            response_msg = await self._llm.ainvoke([
                SystemMessage(content="You are a psychological profiler. Respond only with valid JSON."),
                HumanMessage(content=prompt),
            ])
            
            import json
            analysis = json.loads(response_msg.content)
            
            # Convert analysis to packets
            for key, data in analysis.items():
                if isinstance(data, dict) and data.get("confidence", 0) > 0.3:
                    packet = create_hypothesis_packet(
                        source_agent="genesis.profiler.deep",
                        trait_name=key,
                        suspected_value=data.get("value", "unknown"),
                        confidence=data.get("confidence", 0.5),
                        evidence=[data.get("evidence", "")],
                        session_id=state.session_id,
                    )
                    packets.append(packet)
            
        except Exception as e:
            logger.error(f"[Profiler] Deep analysis error: {e}")
        
        return packets
    
    def get_detection_summary(self, state: GenesisState) -> dict:
        """Get a summary of all detected traits."""
        rubric = state.rubric
        
        return {
            "human_design": {
                "type": rubric.hd_type.to_dict() if rubric.hd_type else None,
                "strategy": rubric.hd_strategy.to_dict() if rubric.hd_strategy else None,
                "authority": rubric.hd_authority.to_dict() if rubric.hd_authority else None,
            },
            "jungian": {
                "dominant": rubric.jung_dominant.to_dict() if rubric.jung_dominant else None,
                "shadow": rubric.jung_shadow.to_dict() if rubric.jung_shadow else None,
            },
            "somatic": {
                "energy_pattern": rubric.energy_pattern.to_dict() if rubric.energy_pattern else None,
            },
            "core": {
                "wound": rubric.core_wound.to_dict() if rubric.core_wound else None,
                "gift": rubric.core_gift.to_dict() if rubric.core_gift else None,
            },
            "completion": rubric.completion_percentage(),
            "high_confidence_count": len(rubric.get_high_confidence_traits()),
            "needs_probing_count": len(rubric.get_low_confidence_traits()),
        }
