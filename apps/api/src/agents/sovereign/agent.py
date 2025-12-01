"""
Sovereign Agent - The Omniscient Core

This is the main entry point for the Sovereign Agent - the omniscient,
omnipresent AI that serves as the user's primary interface to the entire
Project Sovereign system.

The Sovereign Agent:
━━━━━━━━━━━━━━━━━━━━
1. KNOWS EVERYTHING - Full access to Digital Twin, all modules, all data
2. CAN DO ANYTHING - Tools for actions, delegation for specialized tasks
3. SPEAKS NATURALLY - Personality-driven, context-aware responses
4. GENERATES UI - Dynamic generative components for rich interactions
5. LEARNS CONTINUOUSLY - Adapts to user preferences and patterns

Usage:
    agent = SovereignAgent()
    await agent.initialize(session_id, digital_twin, capabilities)
    
    # Simple interaction
    response = await agent.chat("What's my Human Design type?")
    
    # Streaming
    async for chunk in agent.chat_stream("Tell me about my patterns"):
        print(chunk.content)

@module SovereignAgent
"""

from typing import Optional, Any, Dict, List, Set, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import logging
import asyncio

from .cortex import SovereignCortex, CortexOutput, OutputType
from .memory import SovereignMemory, MemoryLayer
from .tools import SovereignToolkit, ToolResult, ToolResultType
from .router import SovereignRouter, DelegationRequest, DelegationType
from ...shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    AgentCapability,
    PacketPriority,
    create_packet,
)
from ...core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# CONTEXT
# =============================================================================

@dataclass
class SovereignContext:
    """
    The complete context for a Sovereign Agent interaction.
    
    This is passed through all components and contains everything
    the agent needs to understand and respond appropriately.
    """
    # Session
    session_id: str
    turn_number: int = 0
    
    # User Identity
    digital_twin: Dict[str, Any] = field(default_factory=dict)
    enabled_capabilities: Set[AgentCapability] = field(default_factory=set)
    
    # Module Data (cached snapshots)
    module_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Request Context
    current_message: str = ""
    conversation_summary: str = ""
    
    # HRM Configuration
    hrm_enabled: bool = False
    hrm_config: Optional[Dict[str, Any]] = None
    
    # Model Configuration
    models_config: Optional[Dict[str, str]] = None
    
    @classmethod
    def from_request(
        cls,
        session_id: str,
        message: str,
        digital_twin: Optional[Dict] = None,
        enabled_capabilities: Optional[List[str]] = None,
        module_data: Optional[Dict] = None,
        hrm_config: Optional[Dict] = None,
        models_config: Optional[Dict] = None,
    ) -> "SovereignContext":
        """Create context from an API request."""
        caps = set()
        if enabled_capabilities:
            for cap_str in enabled_capabilities:
                try:
                    caps.add(AgentCapability(cap_str))
                except ValueError:
                    logger.warning(f"Unknown capability: {cap_str}")
        
        return cls(
            session_id=session_id,
            digital_twin=digital_twin or {},
            enabled_capabilities=caps,
            module_data=module_data or {},
            current_message=message,
            hrm_enabled=bool(hrm_config and hrm_config.get("enabled")),
            hrm_config=hrm_config,
            models_config=models_config,
        )


# =============================================================================
# RESPONSE
# =============================================================================

@dataclass
class SovereignResponse:
    """
    The response from the Sovereign Agent.
    
    Contains text, UI components, and metadata for the frontend to render.
    """
    # Content
    text: str
    components: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tool usage
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Needs user action
    needs_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    confirmation_options: Optional[List[str]] = None
    
    # Suggestions for next actions
    suggestions: List[str] = field(default_factory=list)
    
    # Metadata
    session_id: str = ""
    turn_number: int = 0
    model_used: Optional[str] = None
    processing_time_ms: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "components": self.components,
            "tool_calls": self.tool_calls,
            "needs_confirmation": self.needs_confirmation,
            "confirmation_prompt": self.confirmation_prompt,
            "confirmation_options": self.confirmation_options,
            "suggestions": self.suggestions,
            "session_id": self.session_id,
            "turn_number": self.turn_number,
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms,
        }
    
    def to_streaming_dict(self) -> Dict[str, Any]:
        """Format for SSE streaming."""
        return {
            "type": "response",
            "payload": self.to_dict(),
        }


# =============================================================================
# SOVEREIGN AGENT
# =============================================================================

class SovereignAgent:
    """
    The Omniscient Core of Project Sovereign.
    
    This is the main agent class that:
    - Coordinates all sub-components (Memory, Cortex, Tools, Router)
    - Provides a unified API for chat interactions
    - Manages session state
    - Handles tool execution and delegation
    
    Lifecycle:
        1. Create: agent = SovereignAgent()
        2. Initialize: await agent.initialize(session_id, digital_twin, capabilities)
        3. Chat: response = await agent.chat(message)
        4. Repeat step 3 for ongoing conversation
    
    The agent maintains state across turns within a session, enabling
    contextual, multi-turn conversations.
    """
    
    def __init__(self, model: Optional[str] = None):
        """Create a new Sovereign Agent."""
        self.model = model or settings.PRIMARY_MODEL
        
        # Core components (initialized on first use)
        self._memory: Optional[SovereignMemory] = None
        self._toolkit: Optional[SovereignToolkit] = None
        self._cortex: Optional[SovereignCortex] = None
        self._router: Optional[SovereignRouter] = None
        
        # System integrations (the nervous system)
        self._integrations = None
        
        # State
        self._initialized = False
        self._session_id: Optional[str] = None
    
    @property
    def memory(self) -> SovereignMemory:
        if self._memory is None:
            self._memory = SovereignMemory()
        return self._memory
    
    @property
    def toolkit(self) -> SovereignToolkit:
        if self._toolkit is None:
            self._toolkit = SovereignToolkit()
            self._toolkit.register_defaults()
        return self._toolkit
    
    @property
    def cortex(self) -> SovereignCortex:
        if self._cortex is None:
            self._cortex = SovereignCortex(
                memory=self.memory,
                toolkit=self.toolkit,
                model=self.model,
            )
        return self._cortex
    
    @property
    def router(self) -> SovereignRouter:
        if self._router is None:
            self._router = SovereignRouter()
        return self._router
    
    @property
    def integrations(self):
        """Access to all system integrations (HRM, SwarmBus, Genesis, etc.)."""
        return self._integrations
    
    async def initialize(
        self,
        session_id: Optional[str] = None,
        digital_twin: Optional[Dict[str, Any]] = None,
        enabled_capabilities: Optional[List[AgentCapability]] = None,
        module_data: Optional[Dict[str, Dict]] = None,
    ) -> None:
        """
        Initialize the agent for a session.
        
        Args:
            session_id: Unique session identifier (generated if not provided)
            digital_twin: The user's Digital Twin profile data
            enabled_capabilities: List of enabled module capabilities
            module_data: Cached data from enabled modules
        """
        self._session_id = session_id or str(uuid4())
        
        # Initialize system integrations (HRM, SwarmBus, Genesis, Masters, etc.)
        from .integrations import get_integrations
        self._integrations = await get_integrations()
        logger.info(f"[SovereignAgent] Integrations status: {self._integrations.get_status()}")
        
        # Initialize memory with user data
        self.memory.start_session(self._session_id)
        
        if digital_twin:
            self.memory.load_digital_twin(digital_twin)
        else:
            # Try to load from Genesis if available
            try:
                twin = await self._integrations.genesis.get_digital_twin(self._session_id)
                if twin:
                    self.memory.load_digital_twin(twin)
                    logger.info("[SovereignAgent] Loaded Digital Twin from Genesis")
            except Exception as e:
                logger.debug(f"[SovereignAgent] Could not load Digital Twin from Genesis: {e}")
        
        if enabled_capabilities:
            self.memory.load_capabilities(enabled_capabilities)
        
        if module_data:
            for module_id, data in module_data.items():
                cap = self._get_capability_for_module(module_id)
                if cap:
                    self.memory.modules.update(module_id, cap, data)
        
        # Initialize router with SwarmBus
        await self.router.initialize()
        
        # Pass integrations to cortex for deep reasoning
        self.cortex.set_integrations(self._integrations)
        
        self._initialized = True
        logger.info(f"[SovereignAgent] Initialized session: {self._session_id}")
    
    def _get_capability_for_module(self, module_id: str) -> Optional[AgentCapability]:
        """Map module ID to capability."""
        mapping = {
            "nutrition": AgentCapability.FOOD_ANALYSIS,
            "health": AgentCapability.HEALTH_METRICS,
            "finance": AgentCapability.FINANCE,
            "journal": AgentCapability.JOURNALING,
            "human_design": AgentCapability.HUMAN_DESIGN,
        }
        return mapping.get(module_id)
    
    async def chat(
        self,
        message: str,
        context: Optional[SovereignContext] = None,
    ) -> SovereignResponse:
        """
        Process a chat message and return a response.
        
        This is the main entry point for non-streaming interactions.
        
        Args:
            message: The user's message
            context: Optional pre-built context (built from memory if not provided)
        
        Returns:
            SovereignResponse with text, components, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.utcnow()
        turn = self.memory.increment_turn()
        
        # Build context if not provided
        if context is None:
            context = SovereignContext(
                session_id=self._session_id,
                turn_number=turn,
                digital_twin=self.memory.get_digital_twin(),
                enabled_capabilities=self.memory.get_enabled_capabilities(),
                current_message=message,
            )
        
        # Think!
        cortex_output = await self.cortex.think(message, context)
        
        # Build response
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        response = SovereignResponse(
            text=cortex_output.content,
            components=cortex_output.ui_components,
            session_id=self._session_id,
            turn_number=turn,
            model_used=cortex_output.model_used,
            processing_time_ms=processing_time,
        )
        
        # Handle tool results
        if cortex_output.tool_result:
            result = cortex_output.tool_result
            response.tool_calls.append({
                "tool": cortex_output.tool_name,
                "result": result.to_dict(),
            })
            
            if result.result_type == ToolResultType.NEEDS_CONFIRMATION:
                response.needs_confirmation = True
                response.confirmation_prompt = result.confirmation_prompt
                response.confirmation_options = result.confirmation_options
            
            if result.suggestions:
                response.suggestions.extend(result.suggestions)
        
        return response
    
    async def chat_stream(
        self,
        message: str,
        context: Optional[SovereignContext] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a chat message with streaming response.
        
        Yields SSE-compatible dictionaries as the response is generated.
        
        Args:
            message: The user's message
            context: Optional pre-built context
        
        Yields:
            Dictionaries with streaming chunks: {"type": "chunk", "data": "..."}
        """
        logger.info(f"[SovereignAgent] chat_stream called with message: {message[:50]}...")
        
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.utcnow()
        turn = self.memory.increment_turn()
        
        logger.info(f"[SovereignAgent] Starting stream for turn {turn}")
        
        # Build context
        if context is None:
            context = SovereignContext(
                session_id=self._session_id,
                turn_number=turn,
                digital_twin=self.memory.get_digital_twin(),
                enabled_capabilities=self.memory.get_enabled_capabilities(),
                current_message=message,
            )
        
        # Stream from cortex
        full_content = ""
        all_components = []
        all_tool_calls = []
        chunk_count = 0
        
        async for output in self.cortex.think_stream(message, context):
            if output.output_type == OutputType.STREAM_CHUNK:
                chunk_count += 1
                full_content += output.content
                logger.debug(f"[SovereignAgent] Yielding chunk {chunk_count}: {output.content[:30]}...")
                yield {
                    "type": "chunk",
                    "data": output.content,  # Frontend expects 'data' not 'content'
                }
            elif output.output_type == OutputType.UI_COMPONENT:
                all_components.extend(output.ui_components)
                logger.info(f"[SovereignAgent] Got {len(output.ui_components)} UI components")
                # Also stream components in real-time
                for component in output.ui_components:
                    yield {
                        "type": "component",
                        "data": component,
                    }
            elif output.output_type == OutputType.TOOL_CALL:
                if output.tool_name:
                    tool_call = {
                        "tool_name": output.tool_name,
                        "parameters": output.tool_params or {},
                        "result": output.content,
                    }
                    all_tool_calls.append(tool_call)
                    yield {
                        "type": "tool_call",
                        "data": tool_call,
                    }
        
        # Yield final message with metadata
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(f"[SovereignAgent] Stream complete: {chunk_count} chunks, {len(all_components)} components, {processing_time:.0f}ms")
        
        yield {
            "type": "complete",
            "data": {
                "text": full_content,
                "components": all_components,
                "tool_calls": all_tool_calls,
                "session_id": self._session_id,
                "turn_number": turn,
                "processing_time_ms": processing_time,
            },
        }
    
    async def handle_confirmation(
        self,
        confirmed: bool,
        option_selected: Optional[str] = None,
    ) -> SovereignResponse:
        """
        Handle user confirmation for a pending action.
        
        Called when user responds to a needs_confirmation response.
        """
        # Get the pending action from memory
        pending = self.memory.get("pending_confirmation")
        
        if not pending:
            return SovereignResponse(
                text="There's nothing pending confirmation.",
                session_id=self._session_id,
            )
        
        if confirmed:
            # Execute the confirmed action
            tool_name = pending.get("tool_name")
            tool_params = pending.get("tool_params", {})
            
            context = SovereignContext(
                session_id=self._session_id,
                digital_twin=self.memory.get_digital_twin(),
                enabled_capabilities=self.memory.get_enabled_capabilities(),
            )
            
            result = await self.toolkit.execute(tool_name, tool_params, context)
            
            # Clear pending
            self.memory.delete("pending_confirmation")
            
            return SovereignResponse(
                text=result.message,
                components=result.ui_components,
                session_id=self._session_id,
            )
        else:
            # Cancelled
            self.memory.delete("pending_confirmation")
            return SovereignResponse(
                text="Action cancelled.",
                session_id=self._session_id,
            )
    
    async def delegate_to_genesis(
        self,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delegate a message to the Genesis profiler.
        
        Used when the user needs deep profiling rather than general chat.
        """
        result = await self.router.delegate_to_genesis(
            task="Process user message for profiling",
            input_data={"message": message},
            session_id=session_id or self._session_id,
        )
        
        return {
            "delegated_to": "genesis.core",
            "success": result.success,
            "response": result.response,
        }
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        return {
            "session_id": self._session_id,
            "turn_count": self.memory.turn_count,
            "has_profile": bool(self.memory.get_digital_twin()),
            "enabled_capabilities": [
                c.value for c in self.memory.get_enabled_capabilities()
            ],
            "available_tools": [
                t.name for t in self.toolkit.get_all()
            ],
            "available_agents": self.router.get_available_agents(),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_sovereign_agent: Optional[SovereignAgent] = None


async def get_sovereign_agent() -> SovereignAgent:
    """Get the singleton Sovereign Agent instance."""
    global _sovereign_agent
    if _sovereign_agent is None:
        _sovereign_agent = SovereignAgent()
    return _sovereign_agent
