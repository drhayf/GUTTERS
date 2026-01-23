"""
GUTTERS Query Engine

Answer user questions by searching across all profile modules.
Uses LLM to classify questions and generate answers.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from ....core.ai.llm_factory import get_llm
from ....core.activity.logger import get_activity_logger
from ...registry import ModuleRegistry
from ..synthesis.synthesizer import DEFAULT_MODEL, get_user_preferred_model
from .schemas import QueryResponse

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


class QueryEngine:
    """
    Answer questions by searching across all modules.
    
    Uses LLM to:
    1. Classify which modules are relevant to the question
    2. Build context from relevant module data
    3. Generate a personalized answer
    """
    
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        temperature: float = 0.7
    ):
        """
        Initialize query engine.
        
        Args:
            model_id: LLM model to use
            temperature: Sampling temperature
        """
        self.model_id = model_id
        self.temperature = temperature
        self._llm: BaseChatModel | None = None
        self.activity_logger = get_activity_logger()
    
    @property
    def llm(self) -> "BaseChatModel":
        """Lazy-load LLM instance."""
        if self._llm is None:
            self._llm = get_llm(self.model_id, self.temperature)
        return self._llm
    
    async def answer_query(
        self,
        user_id: int,
        question: str,
        db: AsyncSession,
        trace_id: str | None = None
    ) -> QueryResponse:
        """
        Answer a question by searching relevant modules.
        
        Steps:
        1. Classify question to determine relevant modules
        2. Build context from relevant module data
        3. Generate answer with LLM
        4. Return with metadata
        
        Args:
            user_id: User ID
            question: User's question
            db: Database session
            trace_id: Optional trace ID for logging
            
        Returns:
            QueryResponse with answer and metadata
        """
        import uuid
        trace_id = trace_id or str(uuid.uuid4())
        
        # 1. Classify question to find relevant modules
        relevant_modules = await self._classify_question(question, trace_id)
        
        # 2. Get calculated modules for this user
        calculated = await ModuleRegistry.get_calculated_modules_for_user(user_id, db)
        
        # Filter to only modules we have data for
        available_modules = [m for m in relevant_modules if m in calculated]
        
        if not available_modules:
            return QueryResponse(
                question=question,
                answer="I don't have enough profile data to answer this question. Please ensure your birth data is submitted and calculations are complete.",
                modules_consulted=[],
                confidence=0.0,
                model_used=self.model_id,
            )
        
        # 3. Build context from module data
        context = await self._build_context(user_id, available_modules, db)
        
        # 4. Generate answer
        answer, confidence = await self._generate_answer(
            question, 
            context, 
            available_modules,
            trace_id
        )
        
        return QueryResponse(
            question=question,
            answer=answer,
            modules_consulted=available_modules,
            confidence=confidence,
            model_used=self.model_id,
        )
    
    async def _classify_question(
        self, 
        question: str,
        trace_id: str
    ) -> list[str]:
        """
        Determine which modules are relevant to this question.
        
        Uses LLM to classify question intent and map to modules.
        
        Args:
            question: User's question
            trace_id: Trace ID for logging
            
        Returns:
            List of relevant module names
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        
        classification_prompt = f"""Determine which wisdom traditions are relevant to answer this question.

**QUESTION:** {question}

**AVAILABLE SYSTEMS:**
- astrology: Planetary placements, houses, aspects, transits. Good for: personality, timing, life cycles
- human_design: Type, strategy, authority, centers. Good for: decision-making, energy management, purpose
- numerology: Life path, expression, soul urge. Good for: life direction, talents, inner drives

**INSTRUCTIONS:**
Return a JSON array of relevant system names. Include all that apply.
Return ONLY the JSON array, no other text.

**EXAMPLES:**
"Why do I struggle with boundaries?" → ["astrology", "human_design"]
"What's my life purpose?" → ["astrology", "human_design", "numerology"]
"Should I take this job?" → ["human_design"]

Your answer (JSON array only):"""

        try:
            await self.activity_logger.log_activity(
                trace_id=trace_id,
                agent="query.engine",
                activity_type="classify_question",
                details={"question": question[:100]}
            )
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a classifier that determines which wisdom systems are relevant to a question. Respond only with a JSON array."),
                HumanMessage(content=classification_prompt)
            ])
            
            # Parse response
            content = response.content if isinstance(response.content, str) else str(response.content)
            
            # Extract JSON from response
            modules = self._parse_json_list(content)
            
            # Validate module names
            valid_modules = ["astrology", "human_design", "numerology"]
            return [m for m in modules if m in valid_modules]
            
        except Exception as e:
            logger.warning(f"Classification failed, using all modules: {e}")
            return ["astrology", "human_design", "numerology"]
    
    def _parse_json_list(self, content: str) -> list[str]:
        """
        Parse JSON list from LLM response.
        
        Args:
            content: LLM response content
            
        Returns:
            Parsed list of strings
        """
        try:
            # Try direct parse
            if content.strip().startswith("["):
                return json.loads(content.strip())
            
            # Try to find JSON in content
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            
            return []
        except json.JSONDecodeError:
            return []
    
    async def _build_context(
        self,
        user_id: int,
        modules: list[str],
        db: AsyncSession
    ) -> str:
        """
        Build context string from module data.
        
        Args:
            user_id: User ID
            modules: Modules to include
            db: Database session
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for module_name in modules:
            data = await ModuleRegistry.get_user_profile_data(user_id, db, module_name)
            
            if not data:
                continue
            
            context_parts.append(f"\n## {module_name.replace('_', ' ').title()}")
            
            # Format based on module type
            if module_name == "astrology":
                context_parts.append(self._format_astrology_context(data))
            elif module_name == "human_design":
                context_parts.append(self._format_human_design_context(data))
            elif module_name == "numerology":
                context_parts.append(self._format_numerology_context(data))
            else:
                # Generic formatting
                context_parts.append(json.dumps(data, indent=2)[:500])
        
        return "\n".join(context_parts)
    
    def _format_astrology_context(self, data: dict) -> str:
        """Format astrology data for context."""
        lines = []
        
        planets = data.get("planets", [])
        for planet in planets[:5]:  # Top 5 planets
            name = planet.get("name", "Unknown")
            sign = planet.get("sign", "?")
            house = planet.get("house", "?")
            lines.append(f"- {name}: {sign} (House {house})")
        
        if "ascendant" in data:
            asc = data["ascendant"]
            lines.append(f"- Ascendant: {asc.get('sign', '?')}")
        
        return "\n".join(lines)
    
    def _format_human_design_context(self, data: dict) -> str:
        """Format Human Design data for context."""
        lines = [
            f"- Type: {data.get('type', 'Unknown')}",
            f"- Strategy: {data.get('strategy', 'Unknown')}",
            f"- Authority: {data.get('authority', 'Unknown')}",
            f"- Profile: {data.get('profile', 'Unknown')}",
        ]
        
        if "defined_centers" in data:
            lines.append(f"- Defined Centers: {', '.join(data['defined_centers'])}")
        if "open_centers" in data:
            lines.append(f"- Open Centers: {', '.join(data['open_centers'])}")
        
        return "\n".join(lines)
    
    def _format_numerology_context(self, data: dict) -> str:
        """Format numerology data for context."""
        lines = []
        
        if "life_path" in data:
            lp = data["life_path"]
            lines.append(f"- Life Path: {lp.get('number', '?')}")
        if "expression" in data:
            exp = data["expression"]
            lines.append(f"- Expression: {exp.get('number', '?')}")
        if "soul_urge" in data:
            su = data["soul_urge"]
            lines.append(f"- Soul Urge: {su.get('number', '?')}")
        
        return "\n".join(lines)
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
        modules: list[str],
        trace_id: str
    ) -> tuple[str, float]:
        """
        Generate answer using LLM.
        
        Args:
            question: User's question
            context: Profile context
            modules: Modules consulted
            trace_id: Trace ID for logging
            
        Returns:
            Tuple of (answer, confidence)
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        
        answer_prompt = f"""Answer this question using the person's cosmic profile data.

**QUESTION:** {question}

**PROFILE DATA:**
{context}

**INSTRUCTIONS:**
1. Answer warmly and specifically, speaking directly to the person
2. Cite which systems provide each insight (e.g., "Your Projector type (Human Design) suggests...")
3. Draw connections between systems when relevant
4. Be practical and actionable, not just descriptive
5. Keep your answer concise but complete (200-400 words)

Your answer:"""

        try:
            await self.activity_logger.log_activity(
                trace_id=trace_id,
                agent="query.engine",
                activity_type="llm_call_started",
                details={
                    "model": self.model_id,
                    "purpose": "answer_query",
                    "modules": modules,
                }
            )
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a compassionate guide with deep knowledge of astrology, Human Design, and numerology. Answer questions warmly and specifically, helping people understand their cosmic design."),
                HumanMessage(content=answer_prompt)
            ])
            
            answer = response.content if isinstance(response.content, str) else str(response.content)
            
            # Calculate confidence based on context quality
            confidence = self._calculate_confidence(context, modules)
            
            await self.activity_logger.log_llm_call(
                trace_id=trace_id,
                model_id=self.model_id,
                prompt=answer_prompt[:300],
                response=answer[:300],
            )
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            
            await self.activity_logger.log_activity(
                trace_id=trace_id,
                agent="query.engine",
                activity_type="llm_call_failed",
                details={"error": str(e)}
            )
            
            return self._fallback_answer(question, context), 0.3
    
    def _calculate_confidence(self, context: str, modules: list[str]) -> float:
        """
        Calculate confidence score based on available data.
        
        Args:
            context: Built context string
            modules: Modules consulted
            
        Returns:
            Confidence score 0-1
        """
        # Base confidence on number of modules consulted
        module_score = min(len(modules) / 3, 1.0) * 0.5
        
        # Add score based on context richness
        context_score = min(len(context) / 500, 1.0) * 0.5
        
        return round(module_score + context_score, 2)
    
    def _fallback_answer(self, question: str, context: str) -> str:
        """
        Generate fallback answer when LLM fails.
        
        Args:
            question: User's question
            context: Available context
            
        Returns:
            Template-based answer
        """
        return (
            f"I encountered an issue generating a detailed answer to: '{question}'\n\n"
            f"Based on your profile, here's what I can share:\n{context[:500]}\n\n"
            "Please try again later for a more complete analysis."
        )
