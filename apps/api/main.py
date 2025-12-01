import sys
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.routers import health_router, agents_router, chat_router
from src.routers.profiles import router as profiles_router
from src.routers.sovereign import router as sovereign_router
from src.routers.modules import router as modules_router
from src.agents.registry import register_agents
from src.agents.genesis_profiler import GenesisProfilerAgent

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Sovereign] Starting Project Sovereign API...")
    print(f"[Sovereign] LLM Model: {settings.LLM_MODEL}")
    print(f"[Sovereign] HRM Enabled: {settings.HRM.enabled}")
    print(f"[Sovereign] Allowed Origins: {settings.get_allowed_origins()}")
    
    registry = register_agents()
    
    if not registry.get("genesis_profiler"):
        genesis = GenesisProfilerAgent()
        registry.register(genesis)
    
    from src.core.hrm import get_hrm
    hrm = get_hrm()
    print(f"[Sovereign] HRM Operational: {hrm.enabled}")
    
    # Initialize Sovereign Agent
    from src.agents.sovereign import get_sovereign_agent
    sovereign = await get_sovereign_agent()
    print("[Sovereign] Sovereign Agent initialized")
    
    print(f"[Sovereign] Registered agents: {registry.get_agent_names()}")
    print("[Sovereign] API ready!")
    
    yield
    
    print("[Sovereign] Shutting down...")

app = FastAPI(
    title="Project Sovereign API",
    description="AI-native backend for self-mastery and personal transformation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(agents_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(profiles_router, prefix=settings.API_PREFIX)
app.include_router(sovereign_router, prefix=settings.API_PREFIX)
app.include_router(modules_router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {
        "name": "Project Sovereign",
        "version": "1.0.0",
        "status": "operational",
        "api_prefix": settings.API_PREFIX,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.FASTAPI_PORT,
        reload=True,
    )
