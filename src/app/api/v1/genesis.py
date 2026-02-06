"""
Genesis API Endpoints

REST API for interacting with the Genesis hypothesis refinement system.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...modules.intelligence.genesis.engine import get_genesis_engine
from ...modules.intelligence.genesis.probes import ProbePacket, ProbeResponse, ProbeType

router = APIRouter(prefix="/genesis", tags=["genesis"])


# =============================================================================
# Response Schemas
# =============================================================================

class HypothesisResponse(BaseModel):
    """Hypothesis in API response format."""
    id: str
    field: str
    module: str
    suspected_value: str
    confidence: float
    confidence_threshold: float
    priority: float
    needs_probing: bool
    probes_attempted: int
    resolved: bool
    resolution_method: str | None


class ProbeRequest(BaseModel):
    """Request to generate a new probe."""
    user_id: int
    preferred_type: ProbeType | None = None


class ConfirmationResponse(BaseModel):
    """Confirmed field response."""
    field: str
    module: str
    confirmed_value: str
    confidence: float


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/hypotheses/{user_id}",
    response_model=list[HypothesisResponse],
    summary="Get active hypotheses",
    description="Get all active (unresolved) hypotheses for a user."
)
async def get_hypotheses(user_id: int):
    """Get all active hypotheses for a user."""
    engine = get_genesis_engine()
    hypotheses = engine.get_active_hypotheses(user_id)

    return [
        HypothesisResponse(
            id=h.id,
            field=h.field,
            module=h.module,
            suspected_value=h.suspected_value,
            confidence=h.confidence,
            confidence_threshold=h.confidence_threshold,
            priority=h.priority,
            needs_probing=h.needs_probing,
            probes_attempted=h.probes_attempted,
            resolved=h.resolved,
            resolution_method=h.resolution_method,
        )
        for h in hypotheses
    ]


@router.get(
    "/probe/{user_id}",
    response_model=ProbePacket | None,
    summary="Get next probe",
    description="Get the next probe question for highest priority hypothesis."
)
async def get_next_probe(user_id: int, preferred_type: ProbeType | None = None):
    """Get next probe for user."""
    engine = get_genesis_engine()

    # Select hypothesis
    hypothesis = await engine.select_next_hypothesis(user_id)

    if not hypothesis:
        return None

    # Generate probe
    probe = await engine.generate_probe(hypothesis, preferred_type)

    return probe


@router.post(
    "/respond",
    response_model=list[HypothesisResponse],
    summary="Respond to probe",
    description="Submit response to a probe and update confidences."
)
async def respond_to_probe(response: ProbeResponse):
    """Submit response to a probe."""
    engine = get_genesis_engine()

    # Process response
    updated = await engine.process_response(response.probe_id, response)

    if not updated:
        raise HTTPException(status_code=404, detail="Probe not found or no updates made")

    return [
        HypothesisResponse(
            id=h.id,
            field=h.field,
            module=h.module,
            suspected_value=h.suspected_value,
            confidence=h.confidence,
            confidence_threshold=h.confidence_threshold,
            priority=h.priority,
            needs_probing=h.needs_probing,
            probes_attempted=h.probes_attempted,
            resolved=h.resolved,
            resolution_method=h.resolution_method,
        )
        for h in updated
    ]


@router.get(
    "/confirmations/{user_id}",
    response_model=list[ConfirmationResponse],
    summary="Get confirmations",
    description="Get all confirmed fields for a user."
)
async def get_confirmations(user_id: int):
    """Get confirmed fields for a user."""
    engine = get_genesis_engine()
    confirmed = engine.get_confirmed_hypotheses(user_id)

    return [
        ConfirmationResponse(
            field=h.field,
            module=h.module,
            confirmed_value=h.suspected_value,
            confidence=h.confidence,
        )
        for h in confirmed
    ]


@router.post(
    "/initialize/{user_id}",
    response_model=list[HypothesisResponse],
    summary="Initialize hypotheses",
    description="Manually trigger hypothesis creation from current uncertainties."
)
async def initialize_hypotheses(user_id: int, session_id: str = "api"):
    """
    Manually initialize hypotheses for a user.

    Useful for testing or when events aren't working.
    """

    engine = get_genesis_engine()

    # Get current uncertainties from profile
    # This is a simplified version - in production, fetch from DB

    # For now, return existing hypotheses
    hypotheses = engine.get_active_hypotheses(user_id)

    return [
        HypothesisResponse(
            id=h.id,
            field=h.field,
            module=h.module,
            suspected_value=h.suspected_value,
            confidence=h.confidence,
            confidence_threshold=h.confidence_threshold,
            priority=h.priority,
            needs_probing=h.needs_probing,
            probes_attempted=h.probes_attempted,
            resolved=h.resolved,
            resolution_method=h.resolution_method,
        )
        for h in hypotheses
    ]


# =============================================================================
# Conversational API
# =============================================================================

class GenesisConversationRequest(BaseModel):
    """Request for conversational Genesis flow."""
    session_id: str | None = Field(
        default=None,
        description="Session ID. If None, starts new session."
    )
    probe_id: str | None = Field(
        default=None,
        description="Probe being responded to."
    )
    response: ProbeResponse | None = Field(
        default=None,
        description="Response to probe. If None with session_id, returns current probe."
    )
    user_id: int = Field(description="User ID")


class SessionProgressResponse(BaseModel):
    """Progress through session."""
    probes_sent: int
    max_probes: int
    fields_confirmed: int
    fields_remaining: int
    progress_percentage: float


class GenesisConversationResponse(BaseModel):
    """Response from conversational Genesis endpoint."""
    session_id: str
    probe: ProbePacket | None = None
    confirmations: list[ConfirmationResponse] = Field(default_factory=list)
    session_complete: bool = False
    progress: SessionProgressResponse | None = None
    summary: str | None = None
    message: str | None = None


@router.post(
    "/conversation",
    response_model=GenesisConversationResponse,
    summary="Conversational Genesis",
    description="Single endpoint for natural conversation flow. Handles session management automatically."
)
async def genesis_conversation(request: GenesisConversationRequest):
    """
    Conversational Genesis interface.

    Flow:
    1. If no session_id: Start new session, return first probe
    2. If session_id but no response: Return current probe
    3. If session_id + response: Process response, return next probe or summary
    """
    from ...modules.intelligence.genesis.session import (
        get_session_manager,
    )

    engine = get_genesis_engine()
    manager = get_session_manager()

    # Get or create session
    if request.session_id:
        session = await manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        is_new = False
    else:
        session, is_new = await manager.get_or_create_session(request.user_id, engine)

    # If session is already complete
    if session.state == "complete":
        summary = await manager._generate_summary(session, engine)
        return GenesisConversationResponse(
            session_id=session.session_id,
            probe=None,
            session_complete=True,
            summary=summary,
            message="Session already complete."
        )

    # Process response if provided
    confirmations = []
    if request.response:
        result = await manager.process_response(session, request.response, engine)
        confirmations = [
            ConfirmationResponse(**c) for c in result["confirmations"]
        ]

        if result["session_complete"]:
            progress = manager.get_progress(session, engine)
            return GenesisConversationResponse(
                session_id=session.session_id,
                probe=None,
                confirmations=confirmations,
                session_complete=True,
                progress=SessionProgressResponse(**progress.model_dump()),
                summary=result["summary"],
                message="Refinement complete! Your profile has been updated."
            )

        next_probe = result["next_probe"]
    else:
        # Get next (or first) probe
        next_probe = await manager.get_next_probe(session, engine)

    progress = manager.get_progress(session, engine)

    if not next_probe:
        # No more probes available
        session.mark_complete("no_probes_available")
        summary = await manager._generate_summary(session, engine)
        return GenesisConversationResponse(
            session_id=session.session_id,
            probe=None,
            confirmations=confirmations,
            session_complete=True,
            progress=SessionProgressResponse(**progress.model_dump()),
            summary=summary,
        )

    return GenesisConversationResponse(
        session_id=session.session_id,
        probe=next_probe,
        confirmations=confirmations,
        session_complete=False,
        progress=SessionProgressResponse(**progress.model_dump()),
        message="We'd like to learn more about you." if is_new else None,
    )


@router.post(
    "/conversation/{session_id}/end",
    response_model=GenesisConversationResponse,
    summary="End conversation",
    description="End a Genesis session early and get summary."
)
async def end_conversation(session_id: str):
    """End a Genesis session and get summary."""
    from ...modules.intelligence.genesis.session import get_session_manager

    engine = get_genesis_engine()
    manager = get_session_manager()

    session = await manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await manager.complete_session(session, engine, "user_ended")

    return GenesisConversationResponse(
        session_id=session_id,
        probe=None,
        session_complete=True,
        summary=result["summary"],
        message="Session ended by user."
    )

