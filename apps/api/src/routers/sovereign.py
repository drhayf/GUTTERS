"""
Sovereign API Router - HTTP endpoints for the Sovereign Agent

This module exposes the Sovereign Agent via REST and SSE endpoints.

Endpoints:
    POST /sovereign/chat - Synchronous chat interaction
    POST /sovereign/chat/stream - SSE streaming chat
    POST /sovereign/confirm - Handle pending confirmations
    GET  /sovereign/session - Get session info
    GET  /sovereign/tools - List available tools
    GET  /sovereign/agents - List available agents

@module SovereignRouter
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4
import logging
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field

from ..agents.sovereign import (
    SovereignAgent,
    SovereignContext,
    SovereignResponse,
    get_sovereign_agent,
)
from ..shared.protocol import AgentCapability

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sovereign", tags=["sovereign"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SovereignChatRequest(BaseModel):
    """Request body for chat endpoints."""
    message: str = Field(..., description="The user's message")
    session_id: Optional[str] = Field(None, description="Session ID for continuity")
    
    # Context
    digital_twin: Optional[Dict[str, Any]] = Field(None, description="Digital Twin profile")
    enabled_capabilities: Optional[List[str]] = Field(None, description="Enabled module capabilities")
    module_data: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Cached module data")
    
    # Configuration
    hrm_config: Optional[Dict[str, Any]] = Field(None, description="HRM configuration")
    models_config: Optional[Dict[str, str]] = Field(None, description="Model configuration")


class SovereignConfirmRequest(BaseModel):
    """Request body for confirmation handling."""
    session_id: str
    confirmed: bool
    option_selected: Optional[str] = None


class SovereignChatResponse(BaseModel):
    """Response from chat endpoint."""
    text: str
    components: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    needs_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    confirmation_options: Optional[List[str]] = None
    suggestions: List[str] = []
    session_id: str
    turn_number: int
    model_used: Optional[str] = None
    processing_time_ms: float


class SessionInfoResponse(BaseModel):
    """Response for session info endpoint."""
    session_id: str
    turn_count: int
    has_profile: bool
    enabled_capabilities: List[str]
    available_tools: List[str]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/chat", response_model=SovereignChatResponse)
async def chat(request: SovereignChatRequest) -> SovereignChatResponse:
    """
    Synchronous chat with the Sovereign Agent.
    
    Returns the complete response after processing.
    Use the streaming endpoint for real-time output.
    """
    logger.info(f"[Sovereign API] Chat request: {request.message[:50]}...")
    
    try:
        agent = await get_sovereign_agent()
        
        # Initialize with context
        capabilities = None
        if request.enabled_capabilities:
            capabilities = []
            for cap_str in request.enabled_capabilities:
                try:
                    capabilities.append(AgentCapability(cap_str))
                except ValueError:
                    logger.warning(f"Unknown capability: {cap_str}")
        
        await agent.initialize(
            session_id=request.session_id,
            digital_twin=request.digital_twin,
            enabled_capabilities=capabilities,
            module_data=request.module_data,
        )
        
        # Build context
        context = SovereignContext.from_request(
            session_id=request.session_id or str(uuid4()),
            message=request.message,
            digital_twin=request.digital_twin,
            enabled_capabilities=request.enabled_capabilities,
            module_data=request.module_data,
            hrm_config=request.hrm_config,
            models_config=request.models_config,
        )
        
        # Chat
        response = await agent.chat(request.message, context)
        
        return SovereignChatResponse(
            text=response.text,
            components=response.components,
            tool_calls=response.tool_calls,
            needs_confirmation=response.needs_confirmation,
            confirmation_prompt=response.confirmation_prompt,
            confirmation_options=response.confirmation_options,
            suggestions=response.suggestions,
            session_id=response.session_id,
            turn_number=response.turn_number,
            model_used=response.model_used,
            processing_time_ms=response.processing_time_ms,
        )
        
    except Exception as e:
        logger.error(f"[Sovereign API] Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: SovereignChatRequest):
    """
    Streaming chat with the Sovereign Agent.
    
    Returns an SSE stream with chunks as they're generated.
    
    Event types:
    - chunk: Text chunk (content: string)
    - complete: Final message with all metadata
    - error: Error occurred
    """
    logger.info(f"[Sovereign API] Stream request: {request.message[:50]}...")
    
    async def generate():
        try:
            agent = await get_sovereign_agent()
            
            # Initialize
            capabilities = None
            if request.enabled_capabilities:
                capabilities = []
                for cap_str in request.enabled_capabilities:
                    try:
                        capabilities.append(AgentCapability(cap_str))
                    except ValueError:
                        pass
            
            await agent.initialize(
                session_id=request.session_id,
                digital_twin=request.digital_twin,
                enabled_capabilities=capabilities,
                module_data=request.module_data,
            )
            
            # Build context
            context = SovereignContext.from_request(
                session_id=request.session_id or str(uuid4()),
                message=request.message,
                digital_twin=request.digital_twin,
                enabled_capabilities=request.enabled_capabilities,
                module_data=request.module_data,
                hrm_config=request.hrm_config,
                models_config=request.models_config,
            )
            
            # Stream response
            async for chunk in agent.chat_stream(request.message, context):
                yield {"data": json.dumps(chunk)}
                
        except Exception as e:
            logger.error(f"[Sovereign API] Stream error: {e}")
            yield {"data": json.dumps({"type": "error", "error": str(e)})}
    
    return EventSourceResponse(generate())


@router.post("/confirm", response_model=SovereignChatResponse)
async def confirm_action(request: SovereignConfirmRequest) -> SovereignChatResponse:
    """
    Handle confirmation for a pending action.
    
    Called when the user responds to a needs_confirmation response.
    """
    try:
        agent = await get_sovereign_agent()
        
        # Ensure same session
        await agent.initialize(session_id=request.session_id)
        
        response = await agent.handle_confirmation(
            confirmed=request.confirmed,
            option_selected=request.option_selected,
        )
        
        return SovereignChatResponse(
            text=response.text,
            components=response.components,
            tool_calls=response.tool_calls,
            needs_confirmation=response.needs_confirmation,
            confirmation_prompt=response.confirmation_prompt,
            confirmation_options=response.confirmation_options,
            suggestions=response.suggestions,
            session_id=response.session_id,
            turn_number=response.turn_number,
            model_used=response.model_used,
            processing_time_ms=response.processing_time_ms,
        )
        
    except Exception as e:
        logger.error(f"[Sovereign API] Confirm error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_info(session_id: str) -> Dict[str, Any]:
    """Get information about a session."""
    try:
        agent = await get_sovereign_agent()
        await agent.initialize(session_id=session_id)
        return agent.get_session_info()
        
    except Exception as e:
        logger.error(f"[Sovereign API] Session info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools() -> Dict[str, Any]:
    """List all available tools."""
    try:
        agent = await get_sovereign_agent()
        
        tools = []
        for tool in agent.toolkit.get_all():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "requires_capability": tool.required_capability.value if tool.required_capability else None,
                "requires_confirmation": tool.requires_confirmation,
            })
        
        return {
            "tools": tools,
            "total_count": len(tools),
        }
        
    except Exception as e:
        logger.error(f"[Sovereign API] List tools error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List all available agents."""
    try:
        agent = await get_sovereign_agent()
        await agent.router.initialize()
        
        return {
            "agents": agent.router.get_available_agents(),
        }
        
    except Exception as e:
        logger.error(f"[Sovereign API] List agents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def list_capabilities() -> Dict[str, Any]:
    """List all available capabilities."""
    return {
        "capabilities": [
            {
                "id": cap.value,
                "name": cap.value.replace("_", " ").title(),
            }
            for cap in AgentCapability
        ],
    }
