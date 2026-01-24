"""
GUTTERS Query Engine

Answer user questions by searching across all profile modules.
Uses LLM to classify questions and generate answers.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_community.callbacks import get_openai_callback

from ....core.ai.llm_factory import get_llm
from ....core.config import settings
from ....core.activity.logger import get_activity_logger
from ....models.embedding import Embedding
from ...registry import ModuleRegistry
from ..synthesis.synthesizer import DEFAULT_MODEL
from ..vector.embedding_service import EmbeddingService
from ..vector.search_engine import VectorSearchEngine
from ..trace.context import TraceContext
from ..trace.models import ToolType
from .schemas import QueryResponse
from src.app.core.llm.config import get_premium_llm, LLMTier, LLMConfig
from src.app.modules.intelligence.generative_ui.generator import ComponentGenerator
from src.app.modules.intelligence.generative_ui.models import ComponentType

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI
    from langchain_core.language_models import BaseChatModel
    from ....core.memory import ActiveMemory

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
        llm: Optional[ChatOpenAI] = None,
        memory: Optional["ActiveMemory"] = None,
        embedding_service: Optional["EmbeddingService"] = None,
        search_engine: Optional["VectorSearchEngine"] = None,
        tier: LLMTier = LLMTier.PREMIUM,
        enable_generative_ui: bool = True,
    ):
        """
        Initialize query engine.
        """
        self.llm = llm or get_premium_llm()
        self.tier = tier
        self.memory = memory
        self.embedding_service = embedding_service or EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())
        self.search_engine = search_engine or VectorSearchEngine()
        self.activity_logger = get_activity_logger()
        self.enable_generative_ui = enable_generative_ui
        self.component_generator = ComponentGenerator() if enable_generative_ui else None

    # Removed lazy-load property as it's now initialized in __init__

    async def answer_query(
        self,
        user_id: int,
        question: str,
        db: AsyncSession,
        trace_id: str | None = None,
        force_fresh: bool = False,
        use_vector_search: bool = True,
    ) -> QueryResponse:
        """
        Answer a question by searching relevant modules with full activity tracing.
        """
        # import time # Removed internal import
        # from langchain_community.callbacks import get_openai_callback # Removed internal import
        # from ..trace.context import TraceContext # Removed internal import
        # from ..trace.models import ToolType # Removed internal import

        # START TRACE
        async with TraceContext() as trace:
            # STEP 0: Check for Interactive Component (Generative UI)
            component_spec = None

            # We need some initial context for the component decision;
            # for now passing empty dict + last n messages from history could happen here
            # but we will do it after memory check if needed, or simply parallelize.
            # To keep it simple and fast, we check basic intent first.

            # STEP 1: Check Active Memory
            trace.think("Checking Active Memory for user's profile and synthesis...")

            from ....core.memory import get_active_memory, get_orchestrator

            memory = get_active_memory()

            start_time = time.time()
            try:
                context_data = await memory.get_full_context(user_id)
                memory_latency = int((time.time() - start_time) * 1000)

                if context_data.get("synthesis"):
                    trace.tool_call(
                        ToolType.ACTIVE_MEMORY,
                        "get_full_context",
                        memory_latency,
                        f"Retrieved synthesis + {len(context_data.get('modules', {}))} modules",
                    )
                else:
                    trace.tool_call(
                        ToolType.ACTIVE_MEMORY, "get_full_context", memory_latency, "No synthesis found (cache miss)"
                    )
            except Exception as e:
                memory_latency = int((time.time() - start_time) * 1000)
                trace.tool_call(
                    ToolType.ACTIVE_MEMORY,
                    "get_full_context",
                    memory_latency,
                    f"Error: {str(e)}",
                    metadata={"error": True},
                )
                context_data = {}

            # STEP 2: Vector Search (if enabled)
            vector_context = {}
            if use_vector_search:
                trace.think("Searching vector embeddings for semantically similar content...")

                try:
                    start_time = time.time()
                    count_result = await db.execute(
                        select(func.count(Embedding.id)).where(Embedding.user_id == user_id)
                    )
                    embedding_count = count_result.scalar() or 0
                    count_latency = int((time.time() - start_time) * 1000)

                    if embedding_count > 0:
                        trace.think(f"Found {embedding_count} embeddings. Performing semantic search...")

                        # Embed query
                        start_time = time.time()
                        query_embedding = await self.embedding_service.embed_text(question)
                        embed_latency = int((time.time() - start_time) * 1000)

                        trace.tool_call(
                            ToolType.VECTOR_SEARCH,
                            "embed_query",
                            embed_latency,
                            f"Generated {len(query_embedding)}-dimensional embedding",
                        )

                        # Search
                        start_time = time.time()
                        search_results = await self.search_engine.hybrid_search(user_id, query_embedding, db, limit=10)
                        search_latency = int((time.time() - start_time) * 1000)

                        total_results = sum(len(v) for v in search_results.values())

                        trace.tool_call(
                            ToolType.VECTOR_SEARCH,
                            "hybrid_search",
                            search_latency,
                            f"Found {total_results} relevant items across {len(search_results)} categories",
                            metadata={"categories": {k: len(v) for k, v in search_results.items()}},
                        )

                        vector_context = {
                            "relevant_journal_entries": search_results.get("journal_entries", [])[:3],
                            "relevant_patterns": search_results.get("patterns", [])[:3],
                            "relevant_syntheses": search_results.get("syntheses", [])[:2],
                        }
                    else:
                        trace.think("No embeddings available yet. Skipping vector search.")
                        trace.tool_call(
                            ToolType.VECTOR_SEARCH,
                            "check_embeddings",
                            count_latency,
                            "No embeddings found (populate job not run yet)",
                        )
                except Exception as e:
                    trace.think(f"Vector search error: {str(e)}. Continuing with cached context only.")

            # 1. Classify question (Existing logic, but we can trace it)
            trace.think("Classifying question intent to optimize context retrieval...")
            relevant_modules = await self._classify_question(question, trace_id or str(uuid.uuid4()))

            # STEP 2.5: Generative UI Decision
            # We do this before generating answer so we can potentially inform the answer
            if self.enable_generative_ui and self.component_generator:
                trace.think("Evaluating need for interactive UI component...")
                try:
                    should_gen, comp_type = await self.component_generator.should_generate_component(
                        question,
                        [],  # conversation_history pass if available
                        context_data,  # user context
                    )

                    if should_gen and comp_type:
                        gen_start = time.time()

                        if comp_type == ComponentType.MOOD_SLIDER:
                            component_spec = await self.component_generator.generate_mood_slider(question, context_data)
                        elif comp_type == ComponentType.MULTI_SLIDER:
                            component_spec = await self.component_generator.generate_multi_slider(
                                question, context_data
                            )
                        elif comp_type == ComponentType.HYPOTHESIS_PROBE:
                            # In real flow we'd identify relevant hypothesis first
                            # For MVP we might skip complex probe generation here unless triggered by specific logic
                            pass

                        gen_latency = int((time.time() - gen_start) * 1000)

                        if component_spec:
                            trace.tool_call(
                                ToolType.GENESIS,
                                "generate_component",
                                gen_latency,
                                f"Generated {comp_type.value} (ID: {component_spec.component_id[:8]})",
                            )
                except Exception as e:
                    logger.error(f"Component generation failed: {e}")
                    trace.think(f"Component generation error: {e}")

            # STEP 3: Build prompt
            trace.think("Building enhanced prompt with all available context...")
            # Convert context_data to the string format expected by _generate_answer
            context_str = await self._build_context_from_data(user_id, relevant_modules, context_data, db)

            # STEP 4: LLM call
            trace.think("Generating response with LLM...")

            start_time = time.time()
            prompt = await self._build_enhanced_prompt(question, context_str, vector_context)

            from langchain_core.messages import SystemMessage, HumanMessage

            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="You are a compassionate cosmic intelligence guide."),
                    HumanMessage(content=prompt),
                ]
            )
            llm_latency = int((time.time() - start_time) * 1000)

            # ENHANCED: Get actual model info from config
            provider, model, config = LLMConfig.get_model_info(self.tier)

            # Estimate tokens
            tokens_in = len(prompt.split()) * 1.3
            tokens_out = len(response.content.split()) * 1.3

            # Calculate cost in AUD
            cost_aud = LLMConfig.estimate_cost(self.tier, int(tokens_in), int(tokens_out), currency="AUD")

            trace.model_call(
                provider=provider,
                model=model,
                temperature=config.temperature,
                tokens_in=int(tokens_in),
                tokens_out=int(tokens_out),
                latency_ms=llm_latency,
                cost_usd=cost_aud,  # Using cost_usd field for AUD value
            )

            answer = response.content

            # STEP 5: Calculate confidence (Override with smarter logic)
            trace.think("Calculating response confidence based on data quality...")
            confidence = self._calculate_confidence_enhanced(context_data, vector_context, trace)
            trace.set_confidence(confidence)

            # STEP 6: Store in conversation history
            try:
                if memory.redis_client:
                    await memory.add_to_history(user_id, question, answer)
            except Exception as e:
                logger.warning(f"Failed to store conversation history: {e}")

            # Get completed trace
            completed_trace = trace.get_trace()

            return QueryResponse(
                question=question,
                answer=answer,
                modules_consulted=relevant_modules,
                confidence=confidence,
                model_used=self.tier,
                sources_used=len(vector_context.get("relevant_journal_entries", []))
                + len(vector_context.get("relevant_patterns", [])),
                trace=completed_trace,
                component=component_spec,  # New: Include component
            )

    async def _build_enhanced_prompt(self, question: str, context: str, vector_context: dict) -> str:
        """Build enhanced prompt with vector context section."""
        vector_sections = []
        if vector_context:
            if vector_context.get("relevant_journal_entries"):
                entries_text = "\n".join(
                    [
                        f"- {entry['content']} (similarity: {entry['similarity']:.0%})"
                        for entry in vector_context["relevant_journal_entries"]
                    ]
                )
                vector_sections.append(f"**Pertinent Journal Entries:**\n{entries_text}")

            if vector_context.get("relevant_patterns"):
                patterns_text = "\n".join(
                    [
                        f"- {pattern['content']} (similarity: {pattern['similarity']:.0%})"
                        for pattern in vector_context["relevant_patterns"]
                    ]
                )
                vector_sections.append(f"**Identified Patterns & Hypotheses:**\n{patterns_text}")

        combined_vector_context = "\n\n".join(vector_sections)

        return f"""Answer this question using the person's cosmic profile data and relevant personal context.

**QUESTION:** {question}

**COSMIC PROFILE:**
{context}

{f"**RELEVANT PERSONAL CONTEXT:**\n{combined_vector_context}" if combined_vector_context else ""}

**INSTRUCTIONS:**
1. Answer warmly and specifically, speaking directly to the person.
2. Cite technical insights from their cosmic profile (e.g., "Your Projector type (Human Design)...") AND correlate them with their personal context (journal entries/patterns) if provided.
3. Draw connections between their design and their lived experience.
4. Be practical and actionable.
5. Keep your answer concise but complete (250-450 words).

Your answer:"""

    def _get_model_info(self) -> tuple[str, str]:
        """Extract provider and model from LLM config."""
        model_name = getattr(self.llm, "model_name", "unknown")
        if "/" in model_name:
            provider, model = model_name.split("/", 1)
        else:
            provider = "unknown"
            model = model_name
        return provider, model

    async def _build_context_from_data(self, user_id, modules, context_data, db):
        """Helper to build context string from data already in hand."""
        context_parts = []
        if context_data.get("synthesis"):
            synthesis = context_data["synthesis"]
            context_parts.append(f"## Master Synthesis\n{synthesis.get('synthesis', '')[:1000]}")

        for module_name in modules:
            if module_name in context_data.get("modules", {}):
                data = context_data["modules"][module_name]
                context_parts.append(f"\n## {module_name.replace('_', ' ').title()}")
                context_parts.append(self._format_module_context(module_name, data))
            else:
                # Fallback to DB for missing pieces
                data = await ModuleRegistry.get_user_profile_data(user_id, db, module_name)
                if data:
                    context_parts.append(f"\n## {module_name.replace('_', ' ').title()}")
                    context_parts.append(self._format_module_context(module_name, data))

        return "\n".join(context_parts)

    def _calculate_confidence_enhanced(self, context: dict, vector_context: dict, trace: TraceContext) -> float:
        """
        Calculate response confidence based on actual data quality.
        """
        confidence = 0.70  # Base confidence

        # Synthesis available
        if context.get("synthesis"):
            confidence += 0.05

        # Vector search quality
        if vector_context.get("relevant_patterns"):
            confidence += 0.05

        if vector_context.get("relevant_journal_entries"):
            confidence += 0.03

        # Observer findings
        observer_count = len(vector_context.get("relevant_patterns", []))
        confidence += min(observer_count * 0.025, 0.10)

        # Cap at 0.95
        confidence = min(confidence, 0.95)
        trace.think(f"Calculated confidence: {confidence:.2f} based on available context quality")
        return round(confidence, 2)

    async def _build_context_from_memory(self, user_id: int, modules: list[str], memory: Any, db: AsyncSession) -> str:
        """
        Build context from Active Memory (fast) with database fallback.

        Tries memory first (<5ms), falls back to database if needed (50-200ms).

        Args:
            user_id: User ID
            modules: Modules to include
            memory: ActiveMemory instance
            db: Database session (fallback)

        Returns:
            Formatted context string
        """
        context_parts = []

        # Try to get full context from memory first
        if memory.redis_client:
            try:
                full_context = await memory.get_full_context(user_id)

                # Include master synthesis if available
                if full_context.get("synthesis"):
                    synthesis = full_context["synthesis"]
                    context_parts.append(f"## Master Synthesis\n{synthesis.get('synthesis', '')[:1000]}")
                    if synthesis.get("themes"):
                        context_parts.append(f"Key Themes: {', '.join(synthesis['themes'])}")

                # Include module data from memory
                for module_name in modules:
                    if module_name in full_context.get("modules", {}):
                        data = full_context["modules"][module_name]
                        context_parts.append(f"\n## {module_name.replace('_', ' ').title()}")
                        context_parts.append(self._format_module_context(module_name, data))

                if context_parts:
                    return "\n".join(context_parts)
            except Exception as e:
                logger.warning(f"Memory context failed, falling back to database: {e}")

        # Fallback to database
        return await self._build_context(user_id, modules, db)

    def _format_module_context(self, module_name: str, data: dict) -> str:
        """Format module data for context based on type."""
        if module_name == "astrology":
            return self._format_astrology_context(data)
        elif module_name == "human_design":
            return self._format_human_design_context(data)
        elif module_name == "numerology":
            return self._format_numerology_context(data)
        else:
            return json.dumps(data, indent=2)[:500]

    async def _classify_question(self, question: str, trace_id: str) -> list[str]:
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
                details={"question": question[:100]},
            )

            response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content="You are a classifier that determines which wisdom systems are relevant to a question. Respond only with a JSON array."
                    ),
                    HumanMessage(content=classification_prompt),
                ]
            )

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

    async def _build_context(self, user_id: int, modules: list[str], db: AsyncSession) -> str:
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
        trace_id: str,
        vector_context: dict | None = None,  # NEW: Optional vector context
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

        # Add vector context if available
        vector_sections = []
        if vector_context:
            if vector_context.get("relevant_journal_entries"):
                entries_text = "\n".join(
                    [
                        f"- {entry['content']} (similarity: {entry['similarity']:.0%})"
                        for entry in vector_context["relevant_journal_entries"]
                    ]
                )
                vector_sections.append(f"**Pertinent Journal Entries:**\n{entries_text}")

            if vector_context.get("relevant_patterns"):
                patterns_text = "\n".join(
                    [
                        f"- {pattern['content']} (similarity: {pattern['similarity']:.0%})"
                        for pattern in vector_context["relevant_patterns"]
                    ]
                )
                vector_sections.append(f"**Identified Patterns & Hypotheses:**\n{patterns_text}")

            if vector_context.get("relevant_syntheses"):
                syntheses_text = "\n".join(
                    [
                        f"- {s['content']} (similarity: {s['similarity']:.0%})"
                        for s in vector_context["relevant_syntheses"]
                    ]
                )
                vector_sections.append(f"**Related Syntheses:**\n{syntheses_text}")

        combined_vector_context = "\n\n".join(vector_sections)

        answer_prompt = f"""Answer this question using the person's cosmic profile data and relevant personal context.

**QUESTION:** {question}

**COSMIC PROFILE:**
{context}

{f"**RELEVANT PERSONAL CONTEXT:**\n{combined_vector_context}" if combined_vector_context else ""}

**INSTRUCTIONS:**
1. Answer warmly and specifically, speaking directly to the person.
2. Cite technical insights from their cosmic profile (e.g., "Your Projector type (Human Design)...") AND correlate them with their personal context (journal entries/patterns) if provided.
3. Draw connections between their design and their lived experience.
4. Be practical and actionable.
5. Keep your answer concise but complete (250-450 words).

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
                },
            )

            response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content="You are a compassionate guide with deep knowledge of astrology, Human Design, and numerology. Answer questions warmly and specifically, helping people understand their cosmic design."
                    ),
                    HumanMessage(content=answer_prompt),
                ]
            )

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
                trace_id=trace_id, agent="query.engine", activity_type="llm_call_failed", details={"error": str(e)}
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
