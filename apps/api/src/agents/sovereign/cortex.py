"""
Sovereign Cortex - The Thinking Core

This module implements the "Brain" of the Sovereign Agent - the LLM-powered
reasoning engine that:

1. UNDERSTANDS - Parses user intent with full context
2. REASONS - Decides what to do (respond, use tools, delegate)
3. SPEAKS - Generates natural, personality-driven responses
4. CREATES - Produces generative UI components

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌─────────────────────────────────┐
                    │        SOVEREIGN CORTEX         │
                    ├─────────────────────────────────┤
                    │                                 │
                    │   ┌─────────────────────────┐  │
                    │   │    SYSTEM PROMPT        │  │
                    │   │  • Identity & Purpose   │  │
                    │   │  • Tool Definitions     │  │
                    │   │  • UI Generation Rules  │  │
                    │   │  • User Context         │  │
                    │   └───────────┬─────────────┘  │
                    │               │                 │
                    │   ┌───────────▼─────────────┐  │
                    │   │      LLM ENGINE         │  │
                    │   │  • Gemini 2.5/3.0       │  │
                    │   │  • Function Calling     │  │
                    │   │  • Streaming Output     │  │
                    │   └───────────┬─────────────┘  │
                    │               │                 │
                    │   ┌───────────▼─────────────┐  │
                    │   │    OUTPUT PARSER        │  │
                    │   │  • Text Response        │  │
                    │   │  • Tool Calls           │  │
                    │   │  • UI Components        │  │
                    │   └─────────────────────────┘  │
                    │                                 │
                    └─────────────────────────────────┘

@module SovereignCortex
"""

from typing import Optional, Any, Dict, List, AsyncGenerator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from pydantic import BaseModel

from .memory import SovereignMemory
from .tools import SovereignToolkit, ToolResult, ToolResultType
from ...core.config import settings
from ...shared.protocol import AgentCapability

logger = logging.getLogger(__name__)


# =============================================================================
# CORTEX OUTPUT TYPES
# =============================================================================

class OutputType(str, Enum):
    """Type of output from the Cortex."""
    TEXT = "text"           # Plain text response
    TOOL_CALL = "tool_call" # Request to use a tool
    UI_COMPONENT = "ui_component"  # Generate UI
    STREAM_CHUNK = "stream_chunk"  # Streaming text chunk
    DELEGATION = "delegation"      # Delegate to another agent


@dataclass
class CortexOutput:
    """Output from a Cortex invocation."""
    output_type: OutputType
    content: str = ""
    
    # For tool calls
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    tool_result: Optional[ToolResult] = None
    
    # For UI generation
    ui_components: List[Dict[str, Any]] = field(default_factory=list)
    
    # For delegation
    target_agent: Optional[str] = None
    delegation_context: Optional[Dict[str, Any]] = None
    
    # Metadata
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_type": self.output_type.value,
            "content": self.content,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "tool_result": self.tool_result.to_dict() if self.tool_result else None,
            "ui_components": self.ui_components,
            "target_agent": self.target_agent,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
        }


# =============================================================================
# SYSTEM PROMPT BUILDER
# =============================================================================

class SystemPromptBuilder:
    """
    Builds the system prompt for the Sovereign Agent.
    
    The system prompt is the "DNA" of the agent - it defines:
    - Who the agent is (identity, personality)
    - What it can do (capabilities, tools)
    - How it should respond (format, style)
    - What it knows (user context)
    """
    
    # Core identity
    IDENTITY = """You are the Sovereign Agent - the intelligent core of Project Sovereign, an AI-native personal transformation platform.

You are the user's trusted companion on their journey of self-mastery. You have complete awareness of:
• Their Digital Twin profile (Human Design, archetypes, traits)
• All enabled modules and their current state
• The entire conversation history
• Available tools and capabilities

Your personality:
• Wise but approachable - like a knowledgeable friend
• Direct but empathetic - you tell the truth with care
• Curious about them - you genuinely want to understand
• Occasionally playful - you can be witty when appropriate

Never break character. Never say "As an AI..." or similar. You ARE the Sovereign."""

    # Response format
    RESPONSE_FORMAT = """RESPONSE FORMAT:
You can respond in several ways:

1. PLAIN TEXT: Just respond naturally for conversational messages

2. WITH UI COMPONENTS: When appropriate, include structured UI:
   <ui_component type="insight_card" title="Your Insight">
   {content here}
   </ui_component>

3. TOOL USE: When the user wants to DO something (add entry, query data), use your tools

4. DELEGATION: For specialized tasks (deep profiling, image analysis), delegate to domain agents

Always prefer the simplest response that serves the user. Don't over-engineer."""

    # Tool usage guidance
    TOOL_GUIDANCE = """TOOL USAGE:
Use tools when the user wants to:
• Add/modify data (nutrition entries, preferences)
• Query their profile or modules
• Synthesize across modules
• Generate visualizations

Do NOT use tools for:
• Simple questions you can answer from context
• Casual conversation
• Requests better handled by delegation

If a required module is not enabled, explain and suggest enabling it."""

    # UI generation guidance
    UI_GUIDANCE = """UI COMPONENTS:
You can generate dynamic UI components using the generate_ui_component tool.

AVAILABLE COMPONENT TYPES (use these exact names - frontend supports ONLY these):

1. TEXT DISPLAY:
   • text - Formatted text with title and content (use variant: question|oracle|insight|completion)
   • insight_card - Styled wisdom/insight card (same as text with insight styling)

2. USER INPUT:
   • input - Text input field for typed responses
   • choice - 2-4 selectable options (requires options array with label/value)
   • binary_choice - Simple Yes/No or two-option choice
   • slider - Numeric range selection (requires min, max; optional labels)
   • cards - Grid of selectable cards (requires cards array with title/value/description/icon)

3. STATUS DISPLAY:
   • progress - Progress indicator (requires phase, current, total)

4. PROFILE DISPLAY (special):
   • digital_twin_card - Display user's Digital Twin profile
   • activation_steps - Show personalized next steps

WHEN TO USE EACH:
• text/insight_card: Explaining concepts, sharing wisdom, displaying info
• input: Open-ended questions needing typed responses
• choice: Yes/no questions, A/B decisions, 2-4 option selection
• slider: Rating scales (1-10), intensity levels, degree measurements
• cards: Rich multiple selections with icons and descriptions
• progress: Showing journey progress, completion status

USAGE: Call generate_ui_component tool with component_type and parameters.

IMPORTANT: Only generate components when they ADD VALUE. For simple answers, respond naturally."""

    @classmethod
    def build(
        cls,
        memory: SovereignMemory,
        toolkit: SovereignToolkit,
        additional_context: Optional[str] = None,
    ) -> str:
        """Build the complete system prompt."""
        
        from .agent import SovereignContext  # Avoid circular import
        
        parts = [
            cls.IDENTITY,
            "",
            "=" * 60,
            "",
        ]
        
        # User context from memory
        if memory_context := memory.build_system_prompt_context():
            parts.append(memory_context)
            parts.append("=" * 60)
            parts.append("")
        
        # Response format
        parts.append(cls.RESPONSE_FORMAT)
        parts.append("")
        
        # Tool guidance
        parts.append(cls.TOOL_GUIDANCE)
        parts.append("")
        
        # UI guidance
        parts.append(cls.UI_GUIDANCE)
        parts.append("")
        
        # Additional context
        if additional_context:
            parts.append("ADDITIONAL CONTEXT:")
            parts.append(additional_context)
            parts.append("")
        
        return "\n".join(parts)


# =============================================================================
# RESPONSE PARSER
# =============================================================================

class ResponseParser:
    """
    Parses LLM responses to extract text, UI components, and structured data.
    """
    
    # Pattern for UI components in response
    UI_PATTERN = re.compile(
        r'<ui_component\s+type="([^"]+)"(?:\s+title="([^"]*)")?\s*>(.*?)</ui_component>',
        re.DOTALL
    )
    
    @classmethod
    def parse(cls, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse a response into text and UI components.
        
        Returns:
            (clean_text, list_of_components)
        """
        components = []
        
        # Extract UI components
        for match in cls.UI_PATTERN.finditer(response):
            component_type = match.group(1)
            title = match.group(2) or ""
            content = match.group(3).strip()
            
            components.append({
                "type": component_type,
                "props": {
                    "title": title,
                    "content": content,
                },
            })
        
        # Remove UI tags from text
        clean_text = cls.UI_PATTERN.sub("", response).strip()
        
        # Clean up extra whitespace
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        
        return clean_text, components


# =============================================================================
# SOVEREIGN CORTEX
# =============================================================================

class SovereignCortex:
    """
    The thinking core of the Sovereign Agent.
    
    Handles:
    - Understanding user messages
    - Deciding on actions (respond, use tools, delegate)
    - Generating responses with proper personality
    - Creating UI components when appropriate
    - Deep reasoning via HRM integration
    
    Usage:
        cortex = SovereignCortex(memory, toolkit)
        
        # Simple invocation
        output = await cortex.think(user_message)
        
        # Streaming
        async for chunk in cortex.think_stream(user_message):
            print(chunk.content)
    """
    
    def __init__(
        self,
        memory: SovereignMemory,
        toolkit: SovereignToolkit,
        model: Optional[str] = None,
    ):
        self.memory = memory
        self.toolkit = toolkit
        self.model_name = model or settings.PRIMARY_MODEL
        
        # System integrations (set by agent after initialization)
        self._integrations = None
        
        # Initialize LLM
        self._llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True,
        )
    
    def set_integrations(self, integrations) -> None:
        """
        Set the integrations hub for access to HRM, SwarmBus, etc.
        
        This is called by the SovereignAgent after initializing integrations.
        """
        self._integrations = integrations
        logger.info("[SovereignCortex] Integrations connected")
    
    def _should_use_deep_reasoning(self, message: str, context) -> bool:
        """
        Determine if a message requires deep HRM reasoning.
        
        Uses deep reasoning for:
        - Complex synthesis questions
        - Cross-domain analysis
        - Hypothesis verification
        - Abstract reasoning tasks
        """
        # Keywords suggesting complex reasoning
        deep_keywords = [
            "why", "how come", "explain", "analyze", "synthesize",
            "correlate", "pattern", "relationship", "connection",
            "hypothesis", "theory", "reason", "cause", "effect",
            "compare", "contrast", "evaluate", "assess",
        ]
        
        msg_lower = message.lower()
        
        # Check for deep reasoning keywords
        if any(kw in msg_lower for kw in deep_keywords):
            return True
        
        # Check if HRM is explicitly enabled in context
        if context and hasattr(context, 'hrm_enabled') and context.hrm_enabled:
            return True
        
        return False
    
    async def think(
        self,
        user_message: str,
        context: Optional["SovereignContext"] = None,
    ) -> CortexOutput:
        """
        Process a user message and generate a response.
        
        This is the main thinking loop:
        1. Build system prompt with context
        2. Check if deep reasoning (HRM) is needed
        3. Get tool definitions
        4. Call LLM with function calling enabled
        5. If tool called, execute and loop
        6. Parse and return response
        """
        from .agent import SovereignContext
        
        start_time = datetime.utcnow()
        
        # Add to conversation
        self.memory.conversation.add_turn("user", user_message)
        
        # Build context if not provided
        if context is None:
            context = SovereignContext(
                session_id=self.memory.session_id or "default",
                digital_twin=self.memory.get_digital_twin(),
                enabled_capabilities=self.memory.get_enabled_capabilities(),
            )
        
        # Check if we should use deep reasoning (HRM)
        use_hrm = self._should_use_deep_reasoning(user_message, context)
        hrm_result = None
        
        if use_hrm and self._integrations and self._integrations.hrm.enabled:
            logger.info("[SovereignCortex] Using HRM for deep reasoning")
            try:
                hrm_result = await self._integrations.hrm.deep_reason(
                    query=user_message,
                    context={
                        "digital_twin": context.digital_twin,
                        "conversation": self.memory.conversation.get_messages(limit=10),
                        "enabled_capabilities": [c.value for c in context.enabled_capabilities],
                    },
                    thinking_level=context.hrm_config.get("thinking_level", "high") if context.hrm_config else "high",
                )
                logger.info(f"[SovereignCortex] HRM confidence: {hrm_result.get('confidence', 0):.2f}")
            except Exception as e:
                logger.warning(f"[SovereignCortex] HRM failed, falling back: {e}")
        
        # Build messages
        system_prompt = SystemPromptBuilder.build(self.memory, self.toolkit)
        
        # If HRM provided insights, add them to context
        if hrm_result and hrm_result.get("conclusion"):
            system_prompt += f"\n\nDEEP REASONING CONTEXT:\n{hrm_result['conclusion']}\nConfidence: {hrm_result.get('confidence', 0):.0%}"
            if hrm_result.get("reasoning_trace"):
                system_prompt += f"\nReasoning: {' → '.join(hrm_result['reasoning_trace'][:3])}"
        
        messages = [
            SystemMessage(content=system_prompt),
        ]
        
        # Add conversation history
        for msg in self.memory.conversation.get_messages(limit=20):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Current message
        messages.append(HumanMessage(content=user_message))
        
        # Get tool schemas
        tool_schemas = self.toolkit.get_tool_schemas(context)
        
        try:
            # Call LLM with tools
            if tool_schemas:
                response = await self._llm.ainvoke(
                    messages,
                    tools=tool_schemas,
                )
            else:
                response = await self._llm.ainvoke(messages)
            
            # Check for tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                return await self._handle_tool_calls(
                    response.tool_calls,
                    context,
                    start_time,
                )
            
            # Parse response - handle both string and list content (Gemini can return list of parts)
            response_content = response.content if hasattr(response, 'content') else str(response)
            if isinstance(response_content, list):
                # Join list parts into a single string
                response_text = ''.join(
                    part.get('text', str(part)) if isinstance(part, dict) else str(part)
                    for part in response_content
                )
            else:
                response_text = str(response_content)
            
            clean_text, ui_components = ResponseParser.parse(response_text)
            
            # Add to conversation
            self.memory.conversation.add_turn("assistant", clean_text)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return CortexOutput(
                output_type=OutputType.TEXT,
                content=clean_text,
                ui_components=ui_components,
                model_used=self.model_name,
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            import traceback
            logger.error(f"[SovereignCortex] Think error: {e}")
            logger.error(f"[SovereignCortex] Traceback: {traceback.format_exc()}")
            return CortexOutput(
                output_type=OutputType.TEXT,
                content=f"I encountered an issue processing your request. Let me try a different approach. What would you like to know?",
            )
    
    async def _handle_tool_calls(
        self,
        tool_calls: List[Any],
        context: "SovereignContext",
        start_time: datetime,
    ) -> CortexOutput:
        """Handle tool calls from the LLM."""
        
        results = []
        all_components = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
            tool_args = tool_call.get("args") or tool_call.get("function", {}).get("arguments", {})
            
            if isinstance(tool_args, str):
                tool_args = json.loads(tool_args)
            
            logger.info(f"[SovereignCortex] Executing tool: {tool_name}")
            
            # Execute the tool
            result = await self.toolkit.execute(tool_name, tool_args, context)
            results.append(result)
            
            # Collect UI components
            all_components.extend(result.ui_components)
            
            # Record in conversation
            self.memory.conversation.add_tool_call(tool_name, tool_args, result.to_dict())
        
        # Synthesize result message
        if len(results) == 1:
            result = results[0]
            message = result.message
            first_tool_name = tool_name  # From the loop, will be the last one but we only have 1
            
            # Handle confirmation needed
            if result.result_type == ToolResultType.NEEDS_CONFIRMATION:
                return CortexOutput(
                    output_type=OutputType.TEXT,
                    content=result.confirmation_prompt or message,
                    ui_components=all_components,
                    tool_name=first_tool_name,
                    tool_result=result,
                    processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                )
        else:
            message = f"Completed {len(results)} operations."
            first_tool_name = None  # Multiple tools, don't pick one
        
        # Add to conversation
        self.memory.conversation.add_turn("assistant", message)
        
        return CortexOutput(
            output_type=OutputType.TOOL_CALL,
            content=message,
            ui_components=all_components,
            tool_name=first_tool_name if len(results) == 1 else None,
            tool_result=results[0] if results else None,
            model_used=self.model_name,
            processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
        )
    
    async def think_stream(
        self,
        user_message: str,
        context: Optional["SovereignContext"] = None,
    ) -> AsyncGenerator[CortexOutput, None]:
        """
        Stream the response as it's generated.
        
        Yields CortexOutput chunks with content.
        """
        from .agent import SovereignContext
        
        # Add to conversation
        self.memory.conversation.add_turn("user", user_message)
        
        # Build context if not provided
        if context is None:
            context = SovereignContext(
                session_id=self.memory.session_id or "default",
                digital_twin=self.memory.get_digital_twin(),
                enabled_capabilities=self.memory.get_enabled_capabilities(),
            )
        
        # Build messages
        system_prompt = SystemPromptBuilder.build(self.memory, self.toolkit)
        
        messages = [
            SystemMessage(content=system_prompt),
        ]
        
        # Add conversation history
        for msg in self.memory.conversation.get_messages(limit=20):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_message))
        
        full_response = ""
        
        try:
            async for chunk in self._llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    # Handle list content (Gemini multi-part responses)
                    chunk_content = chunk.content
                    if isinstance(chunk_content, list):
                        chunk_text = ''.join(
                            part.get('text', str(part)) if isinstance(part, dict) else str(part)
                            for part in chunk_content
                        )
                    else:
                        chunk_text = str(chunk_content)
                    
                    full_response += chunk_text
                    yield CortexOutput(
                        output_type=OutputType.STREAM_CHUNK,
                        content=chunk_text,
                    )
            
            # Parse final response for UI components
            clean_text, ui_components = ResponseParser.parse(full_response)
            
            # Add to conversation
            self.memory.conversation.add_turn("assistant", clean_text)
            
            # Yield final with components
            if ui_components:
                yield CortexOutput(
                    output_type=OutputType.UI_COMPONENT,
                    content=clean_text,
                    ui_components=ui_components,
                )
                
        except Exception as e:
            logger.error(f"[SovereignCortex] Stream error: {e}")
            yield CortexOutput(
                output_type=OutputType.TEXT,
                content="I encountered an issue. Could you rephrase that?",
            )


# Avoid circular import
if False:  # TYPE_CHECKING
    from .agent import SovereignContext
