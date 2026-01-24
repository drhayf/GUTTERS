from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional, Dict, Any, List
from pydantic import BaseModel, Field

from src.app.api.dependencies import get_current_user
from src.app.models.user import User
from src.app.core.db.database import async_get_db
from src.app.core.db.database import async_get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.modules.intelligence.generative_ui.models import ComponentResponse, ComponentType
from src.app.core.events.bus import get_event_bus
import uuid
import uuid as uuid_pkg  # alias to avoid conflict if needed, or just use uuid

router = APIRouter(prefix="/chat", tags=["chat"])


# Request/Response models
class SendMessageRequest(BaseModel):
    message: str
    session_id: Optional[int] = None  # For branch sessions


class CreateSessionRequest(BaseModel):
    session_type: str  # 'journal', 'nutrition', etc.
    name: str
    contribute_to_memory: bool = True


class CreateConversationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ChatResponse(BaseModel):
    session_id: int
    message: str
    metadata: Dict[str, Any] = {}
    # Phase 7c will extend this with ui_components


# Master Chat endpoints
@router.post("/master/send", response_model=ChatResponse)
async def send_to_master_chat(
    request: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Send message to Master Chat.

    Returns response with metadata about analysis.
    """
    from src.app.modules.features.chat.master_chat import MasterChatHandler
    from src.app.modules.intelligence.query.engine import QueryEngine
    from src.app.core.memory import get_active_memory
    from src.app.modules.intelligence.synthesis.synthesizer import get_llm

    memory = get_active_memory()
    await memory.initialize()

    query_engine = QueryEngine(get_llm(), memory)
    handler = MasterChatHandler(query_engine)

    result = await handler.send_message(current_user.id, request.message, db)

    return ChatResponse(
        session_id=result["session_id"],
        message=result["message"],
        metadata={
            "modules_consulted": result.get("modules_consulted", []),
            "confidence": result.get("confidence", 0.0),
        },
    )


@router.get("/master/history")
async def get_master_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    limit: int = 50,
):
    """Get Master Chat history."""
    from src.app.modules.features.chat.master_chat import MasterChatHandler
    from src.app.modules.intelligence.query.engine import QueryEngine
    from src.app.core.memory import get_active_memory
    from src.app.modules.intelligence.synthesis.synthesizer import get_llm

    memory = get_active_memory()
    await memory.initialize()

    query_engine = QueryEngine(get_llm(), memory)
    handler = MasterChatHandler(query_engine)

    history = await handler.get_conversation_history(current_user.id, limit, db)

    return {"history": history}


@router.post("/conversation/create")
async def create_master_conversation(
    request: CreateConversationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """Create a new Master Chat conversation."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()
    session = await manager.create_master_conversation(current_user.id, request.name, db)

    return {
        "success": True,
        "data": {
            "id": session.id,
            "name": session.conversation_name,
            "created_at": session.created_at.isoformat(),
        },
        "message": "Conversation created",
    }


@router.get("/conversations")
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """List all Master Chat conversations."""
    from src.app.modules.features.chat.master_chat import MasterChatHandler
    from src.app.modules.intelligence.query.engine import QueryEngine
    from src.app.core.memory import get_active_memory
    from src.app.core.llm.config import get_premium_llm, LLMTier

    memory = get_active_memory()
    await memory.initialize()

    query_engine = QueryEngine(llm=get_premium_llm(), memory=memory, tier=LLMTier.PREMIUM, enable_generative_ui=True)

    handler = MasterChatHandler(query_engine)
    conversations = await handler.get_conversation_list(current_user.id, db)

    return {"success": True, "conversations": conversations}


@router.delete("/conversation/{session_id}")
async def delete_conversation(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """Delete a Master Chat conversation."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()

    try:
        await manager.delete_conversation(session_id, current_user.id, db)
        return {"success": True, "message": "Conversation deleted"}
    except ValueError as e:
        # Return structured error
        return {"success": False, "error": str(e), "code": "DELETE_FAILED"}
        # Or raise HTTPException if strictly following REST, but user requested consistent structure.
        # However, for 400s usually HTTPException is better.
        # I'll stick to returning dict as successful API call with error status as user example showed.
        # Actually user example showed: { "success": false, "error": ... }
        # I'll keep it simple.


@router.post("/conversation/{session_id}/archive")
async def archive_conversation(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """Archive a Master Chat conversation."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()
    session = await manager.archive_conversation(session_id, db)

    return {
        "success": True,
        "data": {
            "id": session.id,
            "archived": session.meta.get("is_archived", False),
        },
        "message": "Conversation archived",
    }


@router.get("/conversation/search")
async def search_conversations(
    q: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    limit: int = 10,
):
    """Search across all conversations."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()
    results = await manager.search_conversations(current_user.id, q, limit, db)

    return {"success": True, "results": results}


# Branch Session endpoints
@router.post("/sessions/create")
async def create_branch_session(
    request: CreateSessionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """Create a branch session (Journal, Nutrition, etc.)."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()
    session = await manager.create_branch_session(
        current_user.id, request.session_type, request.name, request.contribute_to_memory, db
    )

    return {
        "session_id": session.id,
        "session_type": session.session_type,
        "name": session.name,
        "contribute_to_memory": session.contribute_to_memory,
    }


@router.get("/sessions/list")
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    session_type: Optional[str] = None,
):
    """List all sessions for user."""
    from src.app.modules.features.chat.session_manager import SessionManager

    manager = SessionManager()
    sessions = await manager.get_user_sessions(current_user.id, session_type, db)

    return {
        "sessions": [
            {
                "id": s.id,
                "session_type": s.session_type,
                "name": s.name,
                "contribute_to_memory": s.contribute_to_memory,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ]
    }


# Journal Branch endpoints
@router.post("/journal/send", response_model=ChatResponse)
async def send_to_journal(
    request: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """Send message to Journal Branch."""
    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id required for journal")

    from src.app.modules.features.journal.journal_chat import JournalChatHandler

    handler = JournalChatHandler()
    result = await handler.send_message(current_user.id, request.session_id, request.message, db)

    return ChatResponse(session_id=result["session_id"], message=result["message"], metadata=result.get("metadata", {}))


@router.get("/journal/{session_id}/entries")
async def get_journal_entries(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """Get journal entries from session."""
    from src.app.models.user_profile import UserProfile
    from sqlalchemy import select

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalar_one()

    entries = profile.data.get("journal_entries", [])

    return {"entries": entries}


# Generative UI Endpoints
@router.post("/component/submit")
async def submit_component_response(
    response: ComponentResponse,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """
    Submit user response to an interactive component.

    This endpoint is called when the user completes an interaction
    with a UI component (slider, checklist, vote, etc.).
    """

    # Store response in database
    from src.app.models.user_profile import UserProfile
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified

    # Validation logic
    if response.component_type == ComponentType.MULTI_SLIDER:
        if not response.slider_values:
            raise HTTPException(status_code=400, detail="Slider values required for multi-slider")

    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Add to component_responses in UserProfile.data
    # Initialize if missing
    if "component_responses" not in profile.data:
        profile.data["component_responses"] = []

    profile.data["component_responses"].append(response.model_dump(mode="json"))

    # Process response based on component type
    if response.component_type == ComponentType.MOOD_SLIDER and response.slider_value is not None:
        # Add to journal entries with mood score
        if "journal_entries" not in profile.data:
            profile.data["journal_entries"] = []

        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "timestamp": response.submitted_at.isoformat(),
            "content": f"Mood rating: {response.slider_value}/10",  # Using 'content' to match journal schema
            "mood_score": response.slider_value,
            "source": "mood_slider_component",
        }

        profile.data["journal_entries"].append(entry)

        # Publish event for journal entry creation
        event_bus = get_event_bus()
        await event_bus.publish(
            "journal.entry.created",
            {"user_id": current_user.id, "entry_id": entry_id, "content": entry["content"]},
            source="generative_ui.mood_slider",
            user_id=str(current_user.id),
        )

    elif response.component_type == ComponentType.MULTI_SLIDER and response.slider_values:
        # Handle multi-slider (Mood, Energy, Anxiety)
        if "journal_entries" not in profile.data:
            profile.data["journal_entries"] = []

        # Create a rich journal entry from values
        values_str = ", ".join([f"{k.capitalize()}: {v}/10" for k, v in response.slider_values.items()])
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "timestamp": response.submitted_at.isoformat(),
            "content": f"Check-in: {values_str}",
            "scores": response.slider_values,
            "source": "multi_slider_component",
        }

        profile.data["journal_entries"].append(entry)

        # Publish event
        event_bus = get_event_bus()
        await event_bus.publish(
            "journal.entry.created",
            {"user_id": current_user.id, "entry_id": entry_id, "content": entry["content"]},
            source="generative_ui.multi_slider",
            user_id=str(current_user.id),
        )

    # Use flag_modified to ensure sqlalchemy tracks the JSON change
    flag_modified(profile, "data")
    await db.commit()

    return {"success": True, "message": "Response recorded", "component_id": response.component_id}
