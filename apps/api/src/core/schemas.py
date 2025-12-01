from typing import Optional, Any, Literal
from pydantic import BaseModel, Field

class Location(BaseModel):
    latitude: float
    longitude: float

class BirthData(BaseModel):
    date: str
    time: str
    location: Location

class AgentContext(BaseModel):
    birthData: Optional[BirthData] = None
    healthMetrics: Optional[dict[str, Any]] = None
    journalThemes: Optional[list[str]] = None
    userQuery: Optional[str] = None

class AgentInput(BaseModel):
    framework: str
    context: AgentContext

class AgentOutput(BaseModel):
    calculation: Optional[Any] = None
    correlations: Optional[list[str]] = None
    interpretationSeed: str
    visualizationData: Optional[Any] = None
    method: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

InsightType = Literal["Pattern", "Fact", "Suggestion"]

class UniversalProtocolMessage(BaseModel):
    source_agent: str
    target_layer: str = "Orchestrator"
    insight_type: InsightType
    confidence_score: float = Field(ge=0.0, le=1.0)
    payload: dict[str, Any]
    hrm_validated: bool = False


class HRMConfigRequest(BaseModel):
    """HRM configuration from frontend"""
    enabled: Optional[bool] = None
    thinking_level: Optional[Literal["low", "high"]] = None
    h_cycles: Optional[int] = Field(default=None, ge=1, le=4)
    l_cycles: Optional[int] = Field(default=None, ge=1, le=4)
    max_reasoning_depth: Optional[int] = Field(default=None, ge=1, le=16)
    halt_threshold: Optional[float] = Field(default=None, ge=0.5, le=1.0)
    candidate_count: Optional[int] = Field(default=None, ge=2, le=8)
    beam_size: Optional[int] = Field(default=None, ge=1, le=5)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    show_reasoning_trace: Optional[bool] = None
    verbose_logging: Optional[bool] = None


class ModelConfigRequest(BaseModel):
    """Model configuration from frontend - allows selecting models for different purposes."""
    primary_model: Optional[str] = Field(
        default=None, 
        description="Main conversation model"
    )
    fast_model: Optional[str] = Field(
        default=None, 
        description="Real-time operations (pattern detection, probes)"
    )
    synthesis_model: Optional[str] = Field(
        default=None, 
        description="Deep insight generation"
    )
    fallback_model: Optional[str] = Field(
        default=None, 
        description="Backup when others fail"
    )
    auto_fallback: Optional[bool] = Field(
        default=None, 
        description="Automatically try fallback on rate limit"
    )


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    enable_hrm: bool = True
    hrm_config: Optional[HRMConfigRequest] = None
    models_config: Optional[ModelConfigRequest] = None  # Full model configuration
    context: Optional[AgentContext] = None
    model: Optional[str] = None  # Single model override (backward compatibility)
    enabled_capabilities: Optional[list[str]] = Field(
        default=None,
        description="List of enabled module/capability IDs from frontend"
    )

class ChatResponse(BaseModel):
    response: str
    agent_output: Optional[AgentOutput] = None
    protocol_message: Optional[UniversalProtocolMessage] = None
    session_id: str

class AgentManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str
    frameworks: list[str]
    capabilities: list[str] = []
    requires_hrm: bool = False

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    models: dict[str, str] = {}
    hrm_enabled: bool = True

class AgentListResponse(BaseModel):
    agents: list[AgentManifest]
    total: int
