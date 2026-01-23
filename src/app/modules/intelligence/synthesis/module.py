"""
GUTTERS Synthesis Module

Intelligence module for cross-system profile synthesis.
Combines insights from all calculation modules using LLM.
"""
from typing import Any

from ....protocol import MODULE_PROFILE_CALCULATED
from ....protocol.packet import Packet
from ...base import BaseModule
from .synthesizer import ProfileSynthesizer


class SynthesisModule(BaseModule):
    """
    Intelligence module for cross-system synthesis.
    
    Subscribes to:
    - module.profile_calculated: Check if all modules done, trigger synthesis
    
    Provides:
    - Unified profile synthesis across all calculation modules
    """
    
    def __init__(self):
        """Initialize synthesis module."""
        super().__init__()
        self.synthesizer: ProfileSynthesizer | None = None
        self._expected_modules = 3  # astrology, human_design, numerology
    
    async def initialize(self) -> None:
        """Initialize module and subscribe to events."""
        await super().initialize()
        
        # Initialize synthesizer with default model
        from .synthesizer import DEFAULT_MODEL
        self.synthesizer = ProfileSynthesizer(model_id=DEFAULT_MODEL)
    
    async def contribute_to_synthesis(self, user_id: str) -> dict[str, Any]:
        """
        Return data for master synthesis.
        
        This module IS the synthesizer, so it returns its own synthesis.
        
        Args:
            user_id: User UUID
            
        Returns:
            Synthesis data for this user
        """
        return {
            "module": self.name,
            "layer": self.layer,
            "data": {},  # Synthesis data would be here
            "insights": [],
            "metadata": {
                "version": self.version,
            }
        }
    
    async def handle_event(self, packet: Packet) -> None:
        """
        Handle incoming events.
        
        When a calculation module completes, check if all expected
        modules have calculated. If so, trigger synthesis.
        
        Args:
            packet: Event packet
        """
        if packet.event_type == MODULE_PROFILE_CALCULATED:
            await self._handle_profile_calculated(packet)
    
    async def _handle_profile_calculated(self, packet: Packet) -> None:
        """
        Handle profile calculation completion.
        
        Check if all expected modules have calculated for this user.
        If so, trigger synthesis.
        
        Args:
            packet: Event with module calculation data
        """
        user_id = packet.payload.get("user_id")
        module_name = packet.payload.get("module_name")
        
        if not user_id:
            return
        
        # Log the calculation
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Module '{module_name}' calculated for user {user_id}")
        
        # Check if all modules have calculated
        # This is done via the API endpoint, not automatically here
        # to avoid blocking the event loop with heavy synthesis
        
        # The API handles synthesis triggering when ready


# Module instance
module = SynthesisModule()
