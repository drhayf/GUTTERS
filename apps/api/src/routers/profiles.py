"""
Profiles Router - API endpoints for profile and session management.

Provides endpoints for:
- Saving/loading profiles
- Resuming sessions
- Profile listing and management
- Export/import functionality
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import os

from ..storage import get_profile_storage, ProfileSlot


router = APIRouter(prefix="/profiles", tags=["profiles"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SaveProfileRequest(BaseModel):
    """Request to save a profile."""
    session_id: str
    name: str
    slot_id: Optional[str] = None
    # Fallback: frontend can provide session state if backend session is lost
    session_state: Optional[dict] = None
    digital_twin: Optional[dict] = None


class SaveProfileResponse(BaseModel):
    """Response after saving a profile."""
    success: bool
    slot_id: str
    message: str


class ProfileSlotResponse(BaseModel):
    """Profile slot metadata."""
    slot_id: str
    name: str
    status: str
    created_at: str
    updated_at: str
    phase: str
    completion_percentage: float
    total_responses: int
    summary: Optional[str] = None


class ProfileListResponse(BaseModel):
    """List of saved profiles."""
    profiles: List[ProfileSlotResponse]
    total: int
    max_slots: int


class LoadProfileResponse(BaseModel):
    """Response when loading a profile."""
    success: bool
    slot: Optional[ProfileSlotResponse] = None
    session_state: Optional[dict] = None
    digital_twin: Optional[dict] = None
    message: str


class SessionListItem(BaseModel):
    """Session metadata."""
    session_id: str
    saved_at: str
    phase: str
    responses: int


class SessionListResponse(BaseModel):
    """List of saved sessions."""
    sessions: List[SessionListItem]
    total: int


# =============================================================================
# PROFILE ENDPOINTS
# =============================================================================

@router.get("/", response_model=ProfileListResponse)
async def list_profiles():
    """
    List all saved profile slots.
    
    Returns metadata for each saved profile, sorted by most recently updated.
    """
    storage = get_profile_storage()
    slots = storage.list_profiles()
    
    return ProfileListResponse(
        profiles=[
            ProfileSlotResponse(
                slot_id=s.slot_id,
                name=s.name,
                status=s.status.value,
                created_at=s.created_at,
                updated_at=s.updated_at,
                phase=s.phase,
                completion_percentage=s.completion_percentage,
                total_responses=s.total_responses,
                summary=s.summary,
            )
            for s in slots
        ],
        total=len(slots),
        max_slots=storage.MAX_SLOTS,
    )


@router.get("/{slot_id}", response_model=LoadProfileResponse)
async def load_profile(slot_id: str):
    """
    Load a specific profile by slot ID.
    
    Returns the full profile including session state and Digital Twin.
    """
    storage = get_profile_storage()
    profile = storage.load_profile(slot_id)
    
    if not profile:
        return LoadProfileResponse(
            success=False,
            message=f"Profile not found: {slot_id}",
        )
    
    return LoadProfileResponse(
        success=True,
        slot=ProfileSlotResponse(
            slot_id=profile.slot.slot_id,
            name=profile.slot.name,
            status=profile.slot.status.value,
            created_at=profile.slot.created_at,
            updated_at=profile.slot.updated_at,
            phase=profile.slot.phase,
            completion_percentage=profile.slot.completion_percentage,
            total_responses=profile.slot.total_responses,
            summary=profile.slot.summary,
        ),
        session_state=profile.session_state,
        digital_twin=profile.digital_twin,
        message="Profile loaded successfully",
    )


@router.post("/save", response_model=SaveProfileResponse)
async def save_current_profile(request: SaveProfileRequest):
    """
    Save the current session as a profile.
    
    This takes an in-progress or completed session and saves it to a profile slot.
    Supports two modes:
    1. If session exists in backend memory, uses that
    2. If session is lost (server restart), uses frontend-provided session_state fallback
    """
    from ..agents.registry import AgentRegistry
    from ..agents.genesis.state import GenesisState
    
    storage = get_profile_storage()
    registry = AgentRegistry.get_instance()
    genesis = registry.get("genesis_profiler")
    
    if not genesis:
        raise HTTPException(status_code=500, detail="Genesis agent not available")
    
    # Get session state from agent's session manager
    session_state = None
    digital_twin = None
    
    # Try to get from backend session manager first
    if hasattr(genesis, '_session_manager'):
        session = genesis._session_manager.get_session(request.session_id)
        if session:
            session_state = session.genesis_state_dict
            
            # If profile is complete, export Digital Twin
            state = GenesisState.from_dict(session_state)
            if state.profile_complete and hasattr(genesis, '_core'):
                digital_twin = genesis._core.export_digital_twin(state)
    
    # Fallback: use frontend-provided session state (for when backend was restarted)
    if not session_state and request.session_state:
        session_state = request.session_state
        digital_twin = request.digital_twin
        # Log that we used the fallback
        import logging
        logging.info(f"[Profiles] Using frontend-provided session state for {request.session_id}")
    
    if not session_state:
        raise HTTPException(
            status_code=404, 
            detail=f"Session not found: {request.session_id}. Try again or provide session_state in request."
        )
    
    slot_id = storage.save_profile(
        session_state=session_state,
        name=request.name,
        digital_twin=digital_twin,
        slot_id=request.slot_id,
    )
    
    return SaveProfileResponse(
        success=True,
        slot_id=slot_id,
        message=f"Profile saved to {slot_id}",
    )


@router.post("/{slot_id}/resume")
async def resume_profile(slot_id: str):
    """
    Resume a saved profile session.
    
    Creates a new session initialized from the saved profile state.
    Returns the session ID to use for continued interaction.
    """
    from ..agents.registry import AgentRegistry
    import uuid
    
    storage = get_profile_storage()
    profile = storage.load_profile(slot_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {slot_id}")
    
    registry = AgentRegistry.get_instance()
    genesis = registry.get("genesis_profiler")
    
    if not genesis:
        raise HTTPException(status_code=500, detail="Genesis agent not available")
    
    # Create new session from saved state
    new_session_id = str(uuid.uuid4())
    
    if hasattr(genesis, 'restore_session'):
        genesis.restore_session(new_session_id, profile.session_state)
    else:
        # Fallback: just return the state and let frontend handle it
        return {
            "success": True,
            "session_id": new_session_id,
            "restored": False,
            "session_state": profile.session_state,
            "digital_twin": profile.digital_twin,
            "message": "Profile loaded - manual restoration required",
        }
    
    return {
        "success": True,
        "session_id": new_session_id,
        "restored": True,
        "phase": profile.session_state.get("phase"),
        "completion_percentage": profile.session_state.get("completion_percentage"),
        "message": f"Session resumed from profile '{profile.slot.name}'",
    }


@router.delete("/{slot_id}")
async def delete_profile(slot_id: str):
    """
    Delete a saved profile.
    """
    storage = get_profile_storage()
    deleted = storage.delete_profile(slot_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Profile not found: {slot_id}")
    
    return {
        "success": True,
        "slot_id": slot_id,
        "message": "Profile deleted",
    }


# =============================================================================
# SESSION ENDPOINTS
# =============================================================================

@router.get("/sessions/", response_model=SessionListResponse)
async def list_sessions():
    """
    List all saved in-progress sessions.
    """
    storage = get_profile_storage()
    sessions = storage.list_sessions()
    
    return SessionListResponse(
        sessions=[
            SessionListItem(
                session_id=s["session_id"],
                saved_at=s["saved_at"],
                phase=s["phase"],
                responses=s["responses"],
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get a saved session state.
    """
    storage = get_profile_storage()
    session_state = storage.load_session(session_id)
    
    if not session_state:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    return {
        "session_id": session_id,
        "session_state": session_state,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a saved session.
    """
    storage = get_profile_storage()
    deleted = storage.delete_session(session_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Session deleted",
    }


# =============================================================================
# EXPORT/IMPORT ENDPOINTS
# =============================================================================

@router.post("/{slot_id}/export")
async def export_profile(slot_id: str, export_name: Optional[str] = None):
    """
    Export a profile to a downloadable JSON file.
    """
    storage = get_profile_storage()
    filepath = storage.export_profile(slot_id, export_name)
    
    if not filepath:
        raise HTTPException(status_code=404, detail=f"Profile not found: {slot_id}")
    
    return {
        "success": True,
        "filepath": filepath,
        "message": "Profile exported",
    }


@router.get("/{slot_id}/download")
async def download_profile(slot_id: str):
    """
    Download a profile as a JSON file.
    """
    storage = get_profile_storage()
    profile = storage.load_profile(slot_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {slot_id}")
    
    # Export first
    filepath = storage.export_profile(slot_id)
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail="Export failed")
    
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/json",
    )


@router.post("/import")
async def import_profile_upload(
    file: UploadFile = File(...),
    slot_id: Optional[str] = None,
):
    """
    Import a profile from an uploaded JSON file.
    """
    import tempfile
    
    storage = get_profile_storage()
    
    # Save uploaded file temporarily
    try:
        contents = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Import the profile
        imported_slot = storage.import_profile(tmp_path, slot_id)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if not imported_slot:
            raise HTTPException(status_code=400, detail="Invalid profile format")
        
        return {
            "success": True,
            "slot_id": imported_slot,
            "message": f"Profile imported to {imported_slot}",
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exports/")
async def list_exports():
    """
    List all exported profile files.
    """
    storage = get_profile_storage()
    exports = storage.list_exports()
    
    return {
        "exports": exports,
        "total": len(exports),
    }
