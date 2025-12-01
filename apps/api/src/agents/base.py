from abc import ABC, abstractmethod
from typing import Optional
from ..core.schemas import AgentInput, AgentOutput, AgentManifest, UniversalProtocolMessage

class BaseAgent(ABC):
    name: str
    description: str
    frameworks: list[str]
    version: str = "1.0.0"
    capabilities: list[str] = []
    requires_hrm: bool = False
    
    @abstractmethod
    async def execute(
        self, 
        agent_input: AgentInput, 
        model: str = None, 
        session_id: str = None
    ) -> AgentOutput:
        """Execute the agent with optional model override and session tracking."""
        pass
    
    def get_manifest(self) -> AgentManifest:
        return AgentManifest(
            name=self.name,
            version=self.version,
            description=self.description,
            frameworks=self.frameworks,
            capabilities=self.capabilities,
            requires_hrm=self.requires_hrm,
        )
    
    def create_protocol_message(
        self,
        insight_type: str,
        payload: dict,
        confidence: float,
        hrm_validated: bool = False,
    ) -> UniversalProtocolMessage:
        return UniversalProtocolMessage(
            source_agent=self.name,
            target_layer="Orchestrator",
            insight_type=insight_type,
            confidence_score=confidence,
            payload=payload,
            hrm_validated=hrm_validated,
        )
    
    def get_prompt_template(self) -> Optional[str]:
        return None
