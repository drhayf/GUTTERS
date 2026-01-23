"""
GUTTERS Observability API

Endpoints for system observability, tracing, and monitoring.

Provides:
- Event trace retrieval
- Active module monitoring
- Real-time event streaming (SSE)
- Profile completion state
- LLM activity logs
"""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_superuser, get_current_user
from ...core.db.database import async_get_db
from ...core.telemetry.tracer import get_tracer
from ...core.state.tracker import get_state_tracker
from ...core.activity.logger import get_activity_logger

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/trace/{trace_id}")
async def get_trace(
    trace_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Get all events for a trace.
    
    Returns list of events sorted by timestamp.
    
    Args:
        trace_id: Trace ID to retrieve
        
    Returns:
        {"trace_id": str, "events": list[dict], "count": int}
    """
    tracer = get_tracer()
    events = await tracer.get_trace(trace_id)
    
    return {
        "trace_id": trace_id,
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.get("/active-modules")
async def get_active_modules(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Get list of currently active modules.
    
    Scans events from the last 5 minutes to identify active modules.
    
    Returns:
        {"modules": list[str], "count": int}
    """
    tracer = get_tracer()
    modules = await tracer.get_active_modules()
    
    return {
        "modules": modules,
        "count": len(modules),
    }


@router.get("/stream")
async def stream_events(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Stream real-time events via Server-Sent Events (SSE).
    
    Returns an event stream that clients can subscribe to for
    real-time system updates.
    
    Example client:
        const evtSource = new EventSource('/api/v1/observability/stream');
        evtSource.onmessage = (e) => console.log(e.data);
    """
    import asyncio
    import json
    from ...core.events.bus import get_event_bus
    
    async def event_generator():
        """Generate SSE events from event bus."""
        bus = get_event_bus()
        event_queue = asyncio.Queue()
        
        async def queue_handler(packet):
            await event_queue.put(packet)
        
        # Subscribe to all events
        bus.subscribe("*", queue_handler)
        
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for event with timeout
                    packet = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    data = json.dumps(packet.to_dict())
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        except asyncio.CancelledError:
            pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/profile-state/{user_id}")
async def get_profile_state(
    user_id: int,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, Any]:
    """
    Get profile completion state for a user.
    
    Returns completion percentage and domain coverage.
    
    Args:
        user_id: User ID to get state for
        
    Returns:
        {
            "completion_percentage": float,
            "domains": {...domain status...},
            "last_synthesis": datetime,
            "total_data_points": int
        }
    """
    # Allow users to see their own state, or superusers to see any
    if current_user["id"] != user_id and not current_user.get("is_superuser"):
        return {"error": "Not authorized to view this user's state"}
    
    tracker = get_state_tracker()
    state = await tracker.get_profile_state(user_id)
    
    return state


@router.get("/activity/{trace_id}")
async def get_activity(
    trace_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Get LLM activity logs for a trace.
    
    Returns all LLM calls made during this trace.
    
    Args:
        trace_id: Trace ID to retrieve
        
    Returns:
        {"trace_id": str, "activities": list[dict], "count": int}
    """
    logger = get_activity_logger()
    activities = await logger.get_activity(trace_id)
    
    return {
        "trace_id": trace_id,
        "activities": activities,
        "count": len(activities),
    }


@router.get("/recent-events")
async def get_recent_events(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = 100,
) -> dict[str, Any]:
    """
    Get most recent events across all traces.
    
    Args:
        limit: Maximum number of events to return (default 100)
        
    Returns:
        {"events": list[dict], "count": int}
    """
    tracer = get_tracer()
    events = await tracer.get_recent_events(limit=limit)
    
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.get("/health")
async def observability_health(request: Request) -> dict[str, Any]:
    """
    Health check for observability components.
    
    Returns status of tracer, state tracker, and activity logger.
    """
    status = {
        "tracer": "unknown",
        "activity_logger": "unknown",
        "redis": "unknown",
    }
    
    try:
        tracer = get_tracer()
        await tracer.initialize()
        pong = await tracer.redis_client.ping()
        status["tracer"] = "healthy" if pong else "unhealthy"
        status["redis"] = "connected" if pong else "disconnected"
    except Exception as e:
        status["tracer"] = f"error: {e}"
        status["redis"] = "disconnected"
    
    try:
        logger = get_activity_logger()
        await logger.initialize()
        status["activity_logger"] = "healthy"
    except Exception as e:
        status["activity_logger"] = f"error: {e}"
    
    return {
        "status": "healthy" if all(v in ["healthy", "connected"] for v in status.values()) else "degraded",
        "components": status,
    }


@router.get("/genesis-activity/{user_id}")
async def get_genesis_activity(
    user_id: int,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = 50,
) -> dict[str, Any]:
    """
    Get Genesis refinement activity for a user.
    
    Shows probe generation, responses, confidence updates, and confirmations.
    """
    if current_user["id"] != user_id and not current_user.get("is_superuser"):
        return {"error": "Not authorized to view this user's activity"}
    
    logger = get_activity_logger()
    
    # Get activities from genesis agents
    activities = []
    for agent in ["genesis.engine", "genesis.probe_generator", "genesis.session"]:
        agent_activities = await logger.get_activities_by_agent(agent, limit=limit)
        # Filter to this user
        user_activities = [
            a for a in agent_activities 
            if a.get("details", {}).get("user_id") == user_id
        ]
        activities.extend(user_activities)
    
    # Sort by timestamp
    activities.sort(key=lambda a: a.get("timestamp", 0), reverse=True)
    
    # Get genesis status
    tracker = get_state_tracker()
    genesis_status = await tracker.get_genesis_status(user_id)
    
    return {
        "user_id": user_id,
        "genesis_status": genesis_status,
        "activities": activities[:limit],
        "total_probes": len([a for a in activities if a.get("activity_type") == "probe_generated"]),
        "total_responses": len([a for a in activities if a.get("activity_type") == "response_received"]),
    }

