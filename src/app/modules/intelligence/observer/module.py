from typing import Any
from src.app.modules.base import BaseModule
from src.app.modules.intelligence.observer.observer import Observer

class ObserverModule(BaseModule):
    """
    Observer Module (NODE).
    
    Orchestrates pattern detection and provides findings for synthesis.
    """
    
    def __init__(self):
        super().__init__()
        self.brain = Observer()
    
    async def contribute_to_synthesis(self, user_id: str) -> dict[str, Any]:
        """
        Provide detected patterns for master synthesis.
        """
        from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
        
        storage = ObserverFindingStorage()
        findings = await storage.get_findings(int(user_id), min_confidence=0.6)
        
        return {
            "module": self.name,
            "layer": self.layer,
            "data": {
                "findings": findings
            },
            "insights": [f["finding"] for f in findings[:5]],
            "metadata": {
                "version": self.version
            }
        }
    
    async def handle_event(self, packet: Any) -> None:
        """
        Handle events (e.g. trigger re-analysis if needed).
        """
        # Observer is mostly batch/cron based, but could react to events
        pass

# Module instance for registration
module = ObserverModule()
