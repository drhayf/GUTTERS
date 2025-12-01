"""
Hierarchical Reasoning Model (HRM)

An LLM-based reasoning engine inspired by sapientinc/HRM architecture.

Key concepts adapted from the neural architecture:
- H-Level (High-Level): Abstract planning and strategy generation
- L-Level (Low-Level): Detailed execution and candidate scoring
- ACT (Adaptive Computation Time): Dynamic reasoning depth with early halting

This implementation uses LangChain/LangGraph with Google Gemini for reasoning,
rather than the trained transformer approach of the original.
"""

from typing import Optional, Any, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import time

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[HRM] LangGraph not available - using fallback mode")

from .config import settings, HRMConfig


@dataclass
class HLevelState:
    """High-Level planning state - abstract strategies"""
    strategies: List[Dict[str, Any]] = field(default_factory=list)
    current_cycle: int = 0
    planning_complete: bool = False


@dataclass
class LLevelState:
    """Low-Level execution state - detailed computations"""
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    scored_candidates: List[Dict[str, Any]] = field(default_factory=list)
    current_cycle: int = 0
    execution_complete: bool = False


@dataclass
class ReasoningState:
    """Complete HRM reasoning state"""
    query: str
    h_level: HLevelState = field(default_factory=HLevelState)
    l_level: LLevelState = field(default_factory=LLevelState)
    
    # ACT (Adaptive Computation Time) state
    current_step: int = 0
    halt_confidence: float = 0.0
    should_halt: bool = False
    
    # Output
    final_answer: Optional[str] = None
    hrm_validated: bool = False
    reasoning_trace: List[str] = field(default_factory=list)
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class HierarchicalReasoningModel:
    """
    LLM-based Hierarchical Reasoning Model
    
    Implements a two-level reasoning architecture:
    - H-Level: Strategic planning (slow, abstract)
    - L-Level: Tactical execution (fast, detailed)
    
    With Adaptive Computation Time for dynamic depth control.
    """
    
    def __init__(self, config: Optional[HRMConfig] = None):
        self.config = config or settings.HRM
        self.enabled = self.config.enabled and LANGGRAPH_AVAILABLE
        self.llm = None
        self._current_model = settings.LLM_MODEL
        self._setup_llm()
    
    def _setup_llm(self, model: Optional[str] = None) -> None:
        """Initialize the LLM for reasoning"""
        if not settings.GOOGLE_API_KEY:
            self._log("No API key available")
            return
        
        target_model = model or settings.LLM_MODEL
        
        try:
            if LANGGRAPH_AVAILABLE:
                self.llm = ChatGoogleGenerativeAI(
                    model=target_model,
                    temperature=0.7,
                    google_api_key=settings.GOOGLE_API_KEY,
                )
                self._current_model = target_model
                self._log(f"Initialized with model: {target_model}")
        except Exception as e:
            self._log(f"Failed to initialize LLM: {e}")
    
    def _log(self, message: str) -> None:
        """Internal logging helper"""
        if self.config.verbose_logging:
            print(f"[HRM] {message}")
    
    def _add_trace(self, state: ReasoningState, message: str) -> None:
        """Add to reasoning trace if enabled"""
        if self.config.show_reasoning_trace:
            state.reasoning_trace.append(f"[Step {state.current_step}] {message}")
            self._log(message)
    
    # =========================================================================
    # H-LEVEL: High-Level Planning
    # =========================================================================
    
    async def h_level_plan(self, state: ReasoningState) -> ReasoningState:
        """
        H-Level planning phase - generates abstract strategies.
        Runs for h_cycles iterations.
        """
        if not self.llm:
            state.h_level.planning_complete = True
            return state
        
        for cycle in range(self.config.h_cycles):
            state.h_level.current_cycle = cycle + 1
            self._add_trace(state, f"H-Level cycle {cycle + 1}/{self.config.h_cycles}")
            
            try:
                prompt = f"""You are the strategic planning module of a hierarchical reasoning system.

Query: {state.query}

Current strategies: {len(state.h_level.strategies)} generated

Generate {self.config.candidate_count} distinct high-level solution strategies for this query.
Each strategy should be a different conceptual approach.

For each strategy provide:
1. Strategy Name (short)
2. Core Approach (1-2 sentences)
3. Key Steps (bullet points)
4. Strengths & Risks

Format as numbered strategies."""

                response = await self.llm.ainvoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Parse strategies
                strategies = self._parse_strategies(content)
                state.h_level.strategies.extend(strategies)
                
                self._add_trace(state, f"Generated {len(strategies)} strategies")
                
            except Exception as e:
                self._log(f"H-Level error in cycle {cycle + 1}: {e}")
        
        state.h_level.planning_complete = True
        return state
    
    def _parse_strategies(self, content: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured strategies"""
        strategies = []
        sections = content.split("\n\n")
        
        for i, section in enumerate(sections[:self.config.candidate_count]):
            if section.strip():
                strategies.append({
                    "id": i,
                    "content": section.strip(),
                    "score": 0.0,
                })
        
        if not strategies and content.strip():
            strategies.append({
                "id": 0,
                "content": content.strip(),
                "score": 0.0,
            })
        
        return strategies
    
    # =========================================================================
    # L-LEVEL: Low-Level Execution
    # =========================================================================
    
    async def l_level_execute(self, state: ReasoningState) -> ReasoningState:
        """
        L-Level execution phase - scores and refines candidates.
        Runs for l_cycles iterations.
        """
        if not self.llm:
            state.l_level.execution_complete = True
            return state
        
        # Initialize candidates from H-Level strategies
        if not state.l_level.candidates and state.h_level.strategies:
            state.l_level.candidates = [
                {"strategy": s, "score": 0.0, "refined": False}
                for s in state.h_level.strategies
            ]
        
        for cycle in range(self.config.l_cycles):
            state.l_level.current_cycle = cycle + 1
            self._add_trace(state, f"L-Level cycle {cycle + 1}/{self.config.l_cycles}")
            
            try:
                # Score each candidate
                scored = []
                for candidate in state.l_level.candidates:
                    score = await self._score_candidate(state.query, candidate)
                    candidate["score"] = score
                    scored.append(candidate)
                
                # Sort by score and keep top beam_size
                scored.sort(key=lambda x: x["score"], reverse=True)
                state.l_level.candidates = scored[:self.config.beam_size]
                state.l_level.scored_candidates = scored
                
                self._add_trace(state, f"Scored {len(scored)} candidates, kept top {self.config.beam_size}")
                
            except Exception as e:
                self._log(f"L-Level error in cycle {cycle + 1}: {e}")
        
        state.l_level.execution_complete = True
        return state
    
    async def _score_candidate(self, query: str, candidate: Dict[str, Any]) -> float:
        """Score a candidate solution"""
        if not self.llm:
            return 0.5
        
        try:
            strategy = candidate.get("strategy", {})
            content = strategy.get("content", "") if isinstance(strategy, dict) else str(strategy)
            
            prompt = f"""Rate this solution approach from 0.0 to 1.0.

Query: {query}
Approach: {content}

Consider:
- Relevance to the query
- Completeness of the approach
- Logical coherence
- Practical feasibility

Respond with ONLY a decimal number between 0.0 and 1.0."""

            response = await self.llm.ainvoke(prompt)
            text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract score
            score = float(text.strip().split()[0])
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self._log(f"Scoring error: {e}")
            return 0.5
    
    # =========================================================================
    # ACT: Adaptive Computation Time
    # =========================================================================
    
    async def check_halt_condition(self, state: ReasoningState) -> ReasoningState:
        """
        Adaptive Computation Time - decide whether to halt or continue.
        Based on confidence threshold and max reasoning depth.
        """
        state.current_step += 1
        
        # Check max depth
        if state.current_step >= self.config.max_reasoning_depth:
            self._add_trace(state, f"Max depth {self.config.max_reasoning_depth} reached, halting")
            state.should_halt = True
            return state
        
        # Check confidence from scored candidates
        if state.l_level.scored_candidates:
            best_score = state.l_level.scored_candidates[0].get("score", 0.0)
            state.halt_confidence = best_score
            
            if best_score >= self.config.halt_threshold:
                self._add_trace(state, f"Confidence {best_score:.2f} >= threshold {self.config.halt_threshold}, halting")
                state.should_halt = True
                return state
        
        # Check score threshold - if no candidates above minimum, may need to continue
        if state.l_level.scored_candidates:
            max_score = max(c.get("score", 0.0) for c in state.l_level.scored_candidates)
            if max_score < self.config.score_threshold:
                self._add_trace(state, f"Max score {max_score:.2f} below threshold {self.config.score_threshold}, continuing")
                state.should_halt = False
                return state
        
        # Default: continue if under half max depth
        if state.current_step < self.config.max_reasoning_depth // 2:
            self._add_trace(state, f"Step {state.current_step}, continuing...")
            state.should_halt = False
        else:
            state.should_halt = True
        
        return state
    
    # =========================================================================
    # SYNTHESIS: Final Answer Generation
    # =========================================================================
    
    async def synthesize(self, state: ReasoningState) -> ReasoningState:
        """Synthesize final answer from best candidates"""
        if not self.llm:
            state.final_answer = state.query
            return state
        
        try:
            # Gather top candidates
            top_candidates = state.l_level.scored_candidates[:self.config.beam_size]
            
            if not top_candidates:
                state.final_answer = state.query
                return state
            
            candidates_text = "\n\n".join([
                f"Approach {i+1} (score: {c.get('score', 0):.2f}):\n{c.get('strategy', {}).get('content', '')}"
                for i, c in enumerate(top_candidates)
            ])
            
            prompt = f"""Synthesize the best aspects of these approaches into a coherent, well-reasoned response.

Original Query: {state.query}

Top Approaches:
{candidates_text}

Provide a final, synthesized response that:
1. Incorporates the strongest elements from each approach
2. Is coherent and well-structured
3. Directly addresses the original query
4. Is concise but comprehensive"""

            response = await self.llm.ainvoke(prompt)
            state.final_answer = response.content if hasattr(response, 'content') else str(response)
            state.hrm_validated = True
            
            self._add_trace(state, "Synthesis complete")
            
        except Exception as e:
            self._log(f"Synthesis error: {e}")
            # Fallback to best candidate
            if state.l_level.scored_candidates:
                best = state.l_level.scored_candidates[0]
                state.final_answer = best.get("strategy", {}).get("content", state.query)
            else:
                state.final_answer = state.query
        
        return state
    
    # =========================================================================
    # MAIN REASONING LOOP
    # =========================================================================
    
    async def reason(
        self, 
        query: str, 
        max_depth: Optional[int] = None,
        config_override: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main reasoning entry point.
        
        Args:
            query: The user's query to reason about
            max_depth: Override for max reasoning depth
            config_override: Dict of config values to override for this call
            model: Override the LLM model to use for this request
        
        Returns:
            Dict with answer, validation status, and metadata
        """
        # Switch model if a different one is requested
        if model and model != self._current_model:
            self._log(f"Switching model from {self._current_model} to {model}")
            self._setup_llm(model)
        
        # Apply config overrides if provided
        if config_override:
            # Create temporary config with overrides
            config_dict = {
                "enabled": self.config.enabled,
                "thinking_level": self.config.thinking_level,
                "h_cycles": self.config.h_cycles,
                "l_cycles": self.config.l_cycles,
                "max_reasoning_depth": self.config.max_reasoning_depth,
                "halt_threshold": self.config.halt_threshold,
                "candidate_count": self.config.candidate_count,
                "beam_size": self.config.beam_size,
                "score_threshold": self.config.score_threshold,
                "show_reasoning_trace": self.config.show_reasoning_trace,
                "verbose_logging": self.config.verbose_logging,
            }
            
            # Map frontend keys to backend keys
            key_mapping = {
                "thinking_level": "thinking_level",
                "h_cycles": "h_cycles",
                "l_cycles": "l_cycles",
                "max_reasoning_depth": "max_reasoning_depth",
                "halt_threshold": "halt_threshold",
                "candidate_count": "candidate_count",
                "beam_size": "beam_size",
                "score_threshold": "score_threshold",
                "show_reasoning_trace": "show_reasoning_trace",
                "verbose_logging": "verbose_logging",
            }
            
            for key, value in config_override.items():
                if key in key_mapping and value is not None:
                    config_dict[key_mapping[key]] = value
            
            self.config = HRMConfig(**config_dict)
        
        if not self.enabled:
            return {
                "answer": query,
                "hrm_validated": False,
                "depth": 0,
                "reasoning_trace": [],
                "message": "HRM disabled"
            }
        
        start_time = time.time()
        
        # Initialize state
        state = ReasoningState(
            query=query,
            start_time=datetime.now(),
        )
        
        # Override max depth if specified
        if max_depth is not None:
            original_depth = self.config.max_reasoning_depth
            self.config = HRMConfig(
                **{**self.config.__dict__, "max_reasoning_depth": max_depth}
            )
        
        self._add_trace(state, f"Starting HRM reasoning (H-cycles: {self.config.h_cycles}, L-cycles: {self.config.l_cycles})")
        
        try:
            # Main reasoning loop with ACT
            while not state.should_halt and state.current_step < self.config.max_reasoning_depth:
                # H-Level: Strategic planning
                state = await self.h_level_plan(state)
                
                # L-Level: Tactical execution
                state = await self.l_level_execute(state)
                
                # ACT: Check if we should halt
                state = await self.check_halt_condition(state)
            
            # Final synthesis
            state = await self.synthesize(state)
            
        except Exception as e:
            self._log(f"Reasoning error: {e}")
            state.final_answer = query
            state.hrm_validated = False
        
        state.end_time = datetime.now()
        duration_ms = int((time.time() - start_time) * 1000)
        
        return {
            "answer": state.final_answer or query,
            "hrm_validated": state.hrm_validated,
            "depth": state.current_step,
            "confidence": state.halt_confidence,
            "reasoning_trace": state.reasoning_trace,
            "duration_ms": duration_ms,
            "h_cycles_completed": state.h_level.current_cycle,
            "l_cycles_completed": state.l_level.current_cycle,
            "candidates_evaluated": len(state.l_level.scored_candidates),
        }


# ============================================================================
# MODULE-LEVEL INSTANCE
# ============================================================================

_hrm_instance: Optional[HierarchicalReasoningModel] = None


def get_hrm() -> HierarchicalReasoningModel:
    """Get or create the HRM singleton instance"""
    global _hrm_instance
    if _hrm_instance is None:
        _hrm_instance = HierarchicalReasoningModel()
    return _hrm_instance


def reset_hrm() -> HierarchicalReasoningModel:
    """Reset the HRM instance with fresh config"""
    global _hrm_instance
    _hrm_instance = HierarchicalReasoningModel()
    return _hrm_instance
