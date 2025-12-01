from typing import Optional
from fastapi import APIRouter, HTTPException
from ..core.schemas import AgentInput, AgentOutput, AgentListResponse, AgentManifest
from ..agents.registry import AgentRegistry

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=AgentListResponse)
async def list_agents() -> AgentListResponse:
    registry = AgentRegistry.get_instance()
    agents = registry.list_agents()
    return AgentListResponse(agents=agents, total=len(agents))

@router.get("/{agent_name}", response_model=AgentManifest)
async def get_agent(agent_name: str) -> AgentManifest:
    registry = AgentRegistry.get_instance()
    agent = registry.get(agent_name)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    return agent.get_manifest()

@router.post("/{agent_name}/execute", response_model=AgentOutput)
async def execute_agent(agent_name: str, agent_input: AgentInput) -> AgentOutput:
    registry = AgentRegistry.get_instance()
    agent = registry.get(agent_name)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    try:
        result = await agent.execute(agent_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@router.get("/{agent_name}/prompt", response_model=dict)
async def get_agent_prompt(agent_name: str) -> dict:
    registry = AgentRegistry.get_instance()
    agent = registry.get(agent_name)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    prompt = agent.get_prompt_template()
    return {
        "agent": agent_name,
        "prompt_template": prompt,
        "has_prompt": prompt is not None,
    }
