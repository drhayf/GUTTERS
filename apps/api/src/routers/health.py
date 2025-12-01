from fastapi import APIRouter
from ..core.schemas import HealthResponse
from ..core.config import settings
from ..core.hrm import get_hrm

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    hrm = get_hrm()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        models={
            "primary": settings.LLM_MODEL,
            "synthesis": settings.SYNTHESIS_MODEL,
            "fallback": settings.FALLBACK_MODEL,
        },
        hrm_enabled=hrm.enabled,
    )


@router.get("/swarm/status")
async def swarm_status():
    """Get the status of the entire swarm including all Master agents."""
    from ..core.orchestrator import get_swarm_status
    
    try:
        status = await get_swarm_status()
        return {
            "status": "operational",
            "swarm": status,
        }
    except Exception as e:
        return {
            "status": "initializing",
            "error": str(e),
            "message": "Swarm is still initializing. This is normal on first request.",
        }


@router.get("/")
async def root():
    return {
        "name": "Project Sovereign API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": f"{settings.API_PREFIX}/health",
            "swarm_status": f"{settings.API_PREFIX}/swarm/status",
            "agents": f"{settings.API_PREFIX}/agents/",
            "chat": f"{settings.API_PREFIX}/chat/",
        }
    }
