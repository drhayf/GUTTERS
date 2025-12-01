"""
Genesis Swarm Integration - Master Agent Communication

This module handles all communication between Genesis and the Sovereign Swarm:
    - Receiving messages from Master agents (MasterHypothesisEngine, MasterScout)
    - Sending detected patterns to Master agents for cross-domain analysis
    - Handling escalation requests from the Orchestrator

Design Philosophy:
    The Genesis agent is a DOMAIN agent in the swarm hierarchy.
    It sends patterns UP to Master agents for cross-domain correlation,
    and receives insights BACK for enriching the profiling experience.

Communication Flow:
    Genesis ──[patterns]──► MasterHypothesisEngine (cross-domain hypotheses)
    Genesis ──[signals]───► MasterScout (Digital Twin aggregation)
    Genesis ◄──[insights]── Master agents (enriched context)
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import logging
import asyncio

from ...core.swarm_bus import (
    SwarmEnvelope,
    PacketPriority,
    get_bus,
)

if TYPE_CHECKING:
    from .session_manager import GenesisSessionManager

logger = logging.getLogger(__name__)


class GenesisSwarmHandler:
    """
    Handles SwarmBus communication for the Genesis agent.
    
    This class is responsible for:
    1. Receiving messages from Master agents
    2. Routing insights to the correct session
    3. Sending patterns to Master agents for analysis
    
    It maintains a reference to the SessionManager to store
    Master insights in the appropriate session.
    """
    
    def __init__(self, session_manager: "GenesisSessionManager"):
        """
        Initialize with a session manager reference.
        
        Args:
            session_manager: The session manager for storing insights
        """
        self._session_manager = session_manager
        logger.info("[GenesisSwarmHandler] Initialized")
    
    async def handle_message(self, envelope: SwarmEnvelope) -> Optional[Dict[str, Any]]:
        """
        Handle incoming SwarmBus messages.
        
        This is the callback registered with the SwarmBus.
        Routes messages based on source and content.
        
        Args:
            envelope: The SwarmBus message envelope
        
        Returns:
            Acknowledgment dict or None
        """
        source = envelope.source_agent_id
        payload = envelope.payload
        
        logger.info(f"[GenesisSwarmHandler] Received message from {source}")
        
        # Extract session ID if present
        session_id = payload.get("session_id")
        
        if not session_id:
            logger.debug("[GenesisSwarmHandler] No session_id in message, ignoring")
            return {"acknowledged": True, "agent": "genesis.profiler", "processed": False}
        
        # Get session
        session = self._session_manager.get_session(session_id)
        if not session:
            logger.debug(f"[GenesisSwarmHandler] Session not found: {session_id}")
            return {"acknowledged": True, "agent": "genesis.profiler", "session_found": False}
        
        # Route based on source agent
        if "hypothesis" in source.lower() or "master.hypothesis" in source:
            return await self._handle_hypothesis_insight(session_id, source, payload)
        
        elif "scout" in source.lower() or "master.scout" in source:
            return await self._handle_scout_insight(session_id, source, payload)
        
        elif "orchestrator" in source.lower():
            return await self._handle_orchestrator_request(session_id, source, payload)
        
        else:
            logger.debug(f"[GenesisSwarmHandler] Unhandled source: {source}")
            return {"acknowledged": True, "agent": "genesis.profiler"}
    
    async def _handle_hypothesis_insight(
        self,
        session_id: str,
        source: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle insight from MasterHypothesisEngine.
        
        The MasterHypothesis might send:
        - Cross-domain correlations
        - Suggested probes
        - Confidence adjustments
        """
        session = self._session_manager.get_session(session_id)
        if session:
            session.add_master_insight(source, payload)
            logger.info(f"[GenesisSwarmHandler] Stored hypothesis insight for {session_id}")
        
        return {
            "acknowledged": True,
            "agent": "genesis.profiler",
            "insight_stored": True,
            "insight_type": "hypothesis",
        }
    
    async def _handle_scout_insight(
        self,
        session_id: str,
        source: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle insight from MasterScout.
        
        The MasterScout might send:
        - Macro patterns detected
        - Profile coherence alerts
        - Digital Twin updates
        """
        session = self._session_manager.get_session(session_id)
        if session:
            session.add_master_insight(source, payload)
            logger.info(f"[GenesisSwarmHandler] Stored scout insight for {session_id}")
        
        return {
            "acknowledged": True,
            "agent": "genesis.profiler",
            "insight_stored": True,
            "insight_type": "scout",
        }
    
    async def _handle_orchestrator_request(
        self,
        session_id: str,
        source: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle request from Orchestrator.
        
        The Orchestrator might request:
        - Current profile status
        - Specific hypothesis data
        - Phase transition commands
        """
        command = payload.get("command", "status")
        
        if command == "status":
            summary = self._session_manager.get_session_summary(session_id)
            return {
                "acknowledged": True,
                "agent": "genesis.profiler",
                "status": summary,
            }
        
        elif command == "reset":
            self._session_manager.clear_session(session_id)
            return {
                "acknowledged": True,
                "agent": "genesis.profiler",
                "reset": True,
            }
        
        else:
            logger.warning(f"[GenesisSwarmHandler] Unknown orchestrator command: {command}")
            return {
                "acknowledged": True,
                "agent": "genesis.profiler",
                "unknown_command": command,
            }
    
    async def notify_masters(
        self,
        session_id: str,
        hypotheses: list[Dict[str, Any]],
        phase: str,
        completion: float,
        signals: Optional[list[Dict[str, Any]]] = None,
    ) -> None:
        """
        Send detected patterns to Master agents.
        
        Called after each profiling turn to notify Master agents
        of any new patterns that might have cross-domain significance.
        
        Args:
            session_id: The session identifier
            hypotheses: Current active hypotheses
            phase: Current profiling phase
            completion: Profile completion percentage
            signals: Optional list of detected signals
        """
        try:
            bus = await get_bus()
        except Exception as e:
            logger.warning(f"[GenesisSwarmHandler] Failed to get SwarmBus: {e}")
            return
        
        # Notify MasterHypothesisEngine if we have hypotheses
        if hypotheses:
            await self._send_to_hypothesis_master(
                bus, session_id, hypotheses, phase, completion
            )
        
        # Notify MasterScout if we have signals or profile updates
        if signals or completion > 0:
            await self._send_to_scout_master(
                bus, session_id, signals or [], phase, completion
            )
    
    async def _send_to_hypothesis_master(
        self,
        bus,
        session_id: str,
        hypotheses: list[Dict[str, Any]],
        phase: str,
        completion: float,
    ) -> None:
        """Send hypotheses to MasterHypothesisEngine."""
        try:
            await bus.send(
                source_agent_id="genesis.profiler",
                target_capability="hypothesis_aggregation",
                payload={
                    "session_id": session_id,
                    "hypotheses": hypotheses,
                    "phase": phase,
                    "completion": completion,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.NORMAL,
            )
            logger.debug(f"[GenesisSwarmHandler] Sent {len(hypotheses)} hypotheses to MasterHypothesis")
        except Exception as e:
            logger.warning(f"[GenesisSwarmHandler] Failed to notify MasterHypothesis: {e}")
    
    async def _send_to_scout_master(
        self,
        bus,
        session_id: str,
        signals: list[Dict[str, Any]],
        phase: str,
        completion: float,
    ) -> None:
        """Send signals/profile to MasterScout."""
        try:
            await bus.send(
                source_agent_id="genesis.profiler",
                target_capability="profile_aggregation",
                payload={
                    "session_id": session_id,
                    "signals": signals,
                    "phase": phase,
                    "completion": completion,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.NORMAL,
            )
            logger.debug(f"[GenesisSwarmHandler] Sent profile update to MasterScout")
        except Exception as e:
            logger.warning(f"[GenesisSwarmHandler] Failed to notify MasterScout: {e}")
    
    async def escalate_to_orchestrator(
        self,
        session_id: str,
        reason: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Escalate an issue to the Orchestrator.
        
        Used when Genesis encounters something it can't handle alone,
        such as cross-domain conflicts or unclear routing.
        
        Args:
            session_id: The session identifier
            reason: Why we're escalating
            data: Additional context data
        """
        try:
            bus = await get_bus()
            await bus.escalate(
                source_agent_id="genesis.profiler",
                payload={
                    "session_id": session_id,
                    "reason": reason,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.HIGH,
            )
            logger.info(f"[GenesisSwarmHandler] Escalated to Orchestrator: {reason}")
        except Exception as e:
            logger.error(f"[GenesisSwarmHandler] Escalation failed: {e}")

    async def send_digital_twin(
        self,
        session_id: str,
        digital_twin: Dict[str, Any],
    ) -> bool:
        """
        Send the completed Digital Twin to Master Scout for permanent storage.
        
        This is called when Genesis profiling is complete and the user's
        Digital Twin is fully formed. The Master Scout will:
        1. Store the Digital Twin in persistent storage
        2. Index it for cross-domain queries
        3. Notify other agents that this user's profile is available
        
        Args:
            session_id: The session identifier
            digital_twin: The complete Digital Twin export
        
        Returns:
            True if successfully sent, False otherwise
        """
        try:
            bus = await get_bus()
            
            await bus.send(
                source_agent_id="genesis.profiler",
                target_capability="digital_twin_storage",
                payload={
                    "session_id": session_id,
                    "event_type": "profile_complete",
                    "digital_twin": digital_twin,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.HIGH,
            )
            
            logger.info(
                f"[GenesisSwarmHandler] Sent Digital Twin to Master Scout "
                f"(session={session_id[:8]}..., completion={digital_twin.get('completion', 0):.0%})"
            )
            return True
            
        except Exception as e:
            logger.error(f"[GenesisSwarmHandler] Failed to send Digital Twin: {e}")
            return False

    async def broadcast_profile_ready(
        self,
        session_id: str,
        digital_twin_summary: Dict[str, Any],
    ) -> None:
        """
        Broadcast to all domain agents that a user's profile is now available.
        
        This enables profile-aware interactions across the entire swarm.
        Other agents (Finance, Health, Vision) can now query this profile
        to provide personalized responses.
        
        Args:
            session_id: The session identifier
            digital_twin_summary: A condensed version of the Digital Twin
        """
        try:
            bus = await get_bus()
            
            await bus.broadcast(
                source_agent_id="genesis.profiler",
                target_domain=None,  # All domains
                payload={
                    "session_id": session_id,
                    "event_type": "user_profile_ready",
                    "profile_summary": {
                        "hd_type": digital_twin_summary.get("energetic_signature", {}).get("hd_type"),
                        "energy_pattern": digital_twin_summary.get("energetic_signature", {}).get("energy_pattern"),
                        "jung_dominant": digital_twin_summary.get("psychological_profile", {}).get("jung_dominant"),
                        "core_gift": digital_twin_summary.get("psychological_profile", {}).get("core_gift"),
                        "completion": digital_twin_summary.get("completion", 0),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.NORMAL,
            )
            
            logger.info(f"[GenesisSwarmHandler] Broadcast profile_ready for session {session_id[:8]}...")
            
        except Exception as e:
            logger.warning(f"[GenesisSwarmHandler] Broadcast failed: {e}")

    async def broadcast_sophistication_signal(
        self,
        session_id: str,
        sophistication_signal: Dict[str, Any],
    ) -> None:
        """
        Broadcast user sophistication level to all agents.
        
        This is emitted when:
        1. User first crosses the sophistication threshold
        2. Significant changes in sophistication are detected
        
        Other agents can use this to:
        - Adjust their communication style
        - Use deeper/more complex analysis
        - Unlock advanced features
        
        Args:
            session_id: The session identifier
            sophistication_signal: Contains level, score, metrics, threshold_crossed
        """
        try:
            bus = await get_bus()
            
            await bus.broadcast(
                source_agent_id="genesis.profiler",
                target_domain=None,  # All domains
                payload={
                    "session_id": session_id,
                    "event_type": "user_sophistication_update",
                    "sophistication": sophistication_signal,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.NORMAL,
            )
            
            logger.info(
                f"[GenesisSwarmHandler] Broadcast sophistication signal: "
                f"level={sophistication_signal.get('level')}, "
                f"score={sophistication_signal.get('score', 0):.2f}, "
                f"threshold_crossed={sophistication_signal.get('threshold_crossed')}"
            )
            
        except Exception as e:
            logger.warning(f"[GenesisSwarmHandler] Sophistication broadcast failed: {e}")
    
    async def notify_sophistication_threshold_crossed(
        self,
        session_id: str,
        sophistication_signal: Dict[str, Any],
    ) -> None:
        """
        Notify Master agents that the sophistication threshold was crossed.
        
        This is a high-priority notification specifically for:
        - MasterHypothesisEngine: Use deeper analysis patterns
        - MasterScout: Record this milestone in profile
        
        Args:
            session_id: The session identifier
            sophistication_signal: The sophistication signal data
        """
        try:
            bus = await get_bus()
            
            # Notify MasterHypothesisEngine
            await bus.send(
                source_agent_id="genesis.profiler",
                target_capability="hypothesis_aggregation",
                payload={
                    "session_id": session_id,
                    "event_type": "sophistication_threshold_crossed",
                    "sophistication": sophistication_signal,
                    "recommended_voice": sophistication_signal.get("recommended_voice", "sage"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.HIGH,
            )
            
            # Notify MasterScout to record milestone
            await bus.send(
                source_agent_id="genesis.profiler",
                target_capability="profile_aggregation",
                payload={
                    "session_id": session_id,
                    "event_type": "profile_milestone",
                    "milestone_type": "sophistication_threshold_crossed",
                    "sophistication": sophistication_signal,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                priority=PacketPriority.HIGH,
            )
            
            logger.info(
                f"[GenesisSwarmHandler] Notified Masters of threshold crossing "
                f"(recommended_voice={sophistication_signal.get('recommended_voice')})"
            )
            
        except Exception as e:
            logger.warning(f"[GenesisSwarmHandler] Threshold notification failed: {e}")
