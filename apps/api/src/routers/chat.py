import uuid
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..core.schemas import (
    ChatRequest,
    ChatResponse,
    AgentInput,
    AgentContext,
    UniversalProtocolMessage,
)
from ..core.config import settings, AIModels
from ..core.hrm import get_hrm
from ..agents.registry import AgentRegistry

router = APIRouter(prefix="/chat", tags=["chat"])

# Timeout for LLM calls (Gemini 3 with thinking can take 30+ seconds)
AGENT_TIMEOUT_SECONDS = 60

def is_rate_limit_error(error: Exception) -> bool:
    """Check if an error is a rate limit error"""
    error_str = str(error).lower()
    return any(phrase in error_str for phrase in [
        'rate limit', 'quota', '429', 'resource exhausted', 
        'too many requests', 'exceeded'
    ])

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    
    hrm = get_hrm()
    hrm_result = None
    
    if request.enable_hrm and hrm.enabled:
        hrm_result = await hrm.reason(request.message)
    
    registry = AgentRegistry.get_instance()
    genesis = registry.get("genesis_profiler")
    
    agent_output = None
    if genesis:
        agent_input = AgentInput(
            framework="genesis",
            context=request.context or AgentContext(userQuery=request.message),
        )
        if agent_input.context.userQuery is None:
            agent_input.context.userQuery = request.message
        
        try:
            agent_output = await genesis.execute(agent_input)
        except Exception as e:
            print(f"[Chat] Genesis agent error: {e}")
    
    response_text = ""
    if hrm_result and hrm_result.get("answer"):
        response_text = hrm_result["answer"]
    elif agent_output:
        response_text = agent_output.interpretationSeed
    else:
        response_text = f"Received: {request.message}"
    
    protocol_message = None
    if agent_output:
        protocol_message = UniversalProtocolMessage(
            source_agent="Genesis Profiler" if genesis else "System",
            target_layer="Orchestrator",
            insight_type="Pattern",
            confidence_score=agent_output.confidence or 0.5,
            payload={
                "response": response_text[:500],
                "calculation": agent_output.calculation,
            },
            hrm_validated=hrm_result.get("hrm_validated", False) if hrm_result else False,
        )
    
    return ChatResponse(
        response=response_text,
        agent_output=agent_output,
        protocol_message=protocol_message,
        session_id=session_id,
    )

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses using SSE."""
    from ..core.config import ModelConfig
    
    # Build effective model configuration
    # Priority: request.models_config > request.model > settings.MODELS
    if request.models_config:
        # Full model config provided
        model_cfg = ModelConfig(
            primary_model=request.models_config.primary_model or settings.MODELS.primary_model,
            fast_model=request.models_config.fast_model or settings.MODELS.fast_model,
            synthesis_model=request.models_config.synthesis_model or settings.MODELS.synthesis_model,
            fallback_model=request.models_config.fallback_model or settings.MODELS.fallback_model,
            auto_fallback=request.models_config.auto_fallback if request.models_config.auto_fallback is not None else settings.MODELS.auto_fallback,
        ).validate_models()
    elif request.model and AIModels.is_valid(request.model):
        # Single model override (backward compatibility)
        model_cfg = ModelConfig(
            primary_model=request.model,
            fast_model=settings.MODELS.fast_model,
            synthesis_model=settings.MODELS.synthesis_model,
            fallback_model=settings.MODELS.fallback_model,
            auto_fallback=settings.MODELS.auto_fallback,
        )
    else:
        # Use default configuration
        model_cfg = settings.MODELS
    
    # Primary model for this request
    model = model_cfg.primary_model
    
    # Build HRM config override from request
    hrm_config_override = None
    if request.hrm_config:
        hrm_config_override = {
            k: v for k, v in request.hrm_config.model_dump().items() 
            if v is not None
        }
    
    async def generate() -> AsyncGenerator[dict, None]:
        """Generate SSE events as dictionaries.
        
        sse_starlette.EventSourceResponse expects dicts with SSE-specific keys:
        - 'data': The actual data to send (will be JSON-serialized if dict)
        - 'event': Optional event type name
        - 'id': Optional event ID
        - 'retry': Optional retry interval
        - 'comment': Optional comment
        
        We wrap our JSON payloads in {'data': <json_string>} format.
        """
        import json
        
        session_id = request.session_id or str(uuid.uuid4())
        
        # Include full model config in session info
        model_info = {
            'primary': model_cfg.primary_model,
            'fast': model_cfg.fast_model,
            'synthesis': model_cfg.synthesis_model,
            'fallback': model_cfg.fallback_model,
        }
        
        # Yield dicts with 'data' key containing JSON string
        yield {'data': json.dumps({'type': 'session', 'session_id': session_id, 'model': model, 'model_config': model_info})}
        
        hrm = get_hrm()
        if request.enable_hrm and hrm.enabled:
            yield {'data': json.dumps({'type': 'hrm_start', 'model': model})}
            
            try:
                hrm_result = await asyncio.wait_for(
                    hrm.reason(request.message, config_override=hrm_config_override, model=model),
                    timeout=AGENT_TIMEOUT_SECONDS
                )
                
                if hrm_result.get("reasoning_trace"):
                    for trace in hrm_result["reasoning_trace"]:
                        yield {'data': json.dumps({'type': 'hrm_trace', 'content': trace})}
                
                hrm_meta = {
                    'type': 'hrm_complete',
                    'validated': hrm_result.get('hrm_validated', False),
                    'depth': hrm_result.get('depth', 0),
                    'confidence': hrm_result.get('confidence', 0),
                    'duration_ms': hrm_result.get('duration_ms', 0),
                }
                yield {'data': json.dumps(hrm_meta)}
            except asyncio.TimeoutError:
                print(f"[Chat/Stream] HRM timeout after {AGENT_TIMEOUT_SECONDS}s")
                yield {'data': json.dumps({'type': 'hrm_complete', 'validated': False, 'timeout': True})}
        
        registry = AgentRegistry.get_instance()
        genesis = registry.get("genesis_profiler")
        
        if genesis:
            yield {'data': json.dumps({'type': 'agent_start', 'agent': 'Genesis Profiler', 'model': model})}
            
            agent_input = AgentInput(
                framework="genesis",
                context=request.context or AgentContext(userQuery=request.message),
            )
            if agent_input.context.userQuery is None:
                agent_input.context.userQuery = request.message
            
            try:
                print(f"[Chat/Stream] Executing Genesis agent with model: {model}, session_id: {session_id}")
                # Pass model AND session_id to agent execute
                agent_output = await asyncio.wait_for(
                    genesis.execute(agent_input, model=model, session_id=session_id),
                    timeout=AGENT_TIMEOUT_SECONDS
                )
                print(f"[Chat/Stream] Genesis agent completed")
                
                # agent_output is now always an AgentOutput Pydantic model
                output_data = {
                    'interpretationSeed': agent_output.interpretationSeed,
                    'method': agent_output.method,
                    'confidence': agent_output.confidence,
                    'calculation': agent_output.calculation,
                    'correlations': agent_output.correlations,
                    'visualizationData': agent_output.visualizationData
                }
                
                # Emit agent_output with ALL data including visualizationData
                yield {'data': json.dumps({'type': 'agent_output', 'data': output_data})}
                
            except asyncio.TimeoutError:
                print(f"[Chat/Stream] Genesis agent timeout after {AGENT_TIMEOUT_SECONDS}s")
                yield {'data': json.dumps({'type': 'error', 'error_type': 'timeout', 'message': f'Agent timeout after {AGENT_TIMEOUT_SECONDS}s - try a faster model like Gemini 2.5 Flash'})}
            except Exception as e:
                error_msg = str(e)
                print(f"[Chat/Stream] Genesis agent error: {error_msg}")
                
                # Check if it's a rate limit error
                if is_rate_limit_error(e):
                    yield {'data': json.dumps({'type': 'error', 'error_type': 'rate_limit', 'message': f'Rate limit hit for {model}. Please select a different model.', 'model': model})}
                else:
                    yield {'data': json.dumps({'type': 'error', 'error_type': 'general', 'message': error_msg})}
        
        yield {'data': json.dumps({'type': 'complete'})}
    
    return EventSourceResponse(generate())

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    return {
        "session_id": session_id,
        "status": "active",
        "message": "Session state management coming soon",
    }


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a session's state on the backend."""
    registry = AgentRegistry.get_instance()
    genesis = registry.get("genesis_profiler")
    
    cleared = False
    if genesis and hasattr(genesis, 'clear_session'):
        genesis.clear_session(session_id)
        cleared = True
    
    return {
        "session_id": session_id,
        "cleared": cleared,
        "message": f"Session {session_id} cleared" if cleared else "No session found",
    }
