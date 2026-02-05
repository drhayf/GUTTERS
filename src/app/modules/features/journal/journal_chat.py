"""
Journal Branch chat handler.

Focused conversational interface for creating journal entries.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage
import json

from src.app.modules.features.chat.session_manager import SessionManager
from src.app.core.llm.config import get_standard_llm, LLMTier
from src.app.models.user_profile import UserProfile
from sqlalchemy import select
import uuid
from datetime import datetime, timezone as dt_timezone


class JournalChatHandler:
    """
    Journal Branch chat handler.

    Uses Claude Haiku 4.5 (standard tier) for efficient classification
    and mood extraction from journal entries.
    """

    def __init__(self):
        self.session_manager = SessionManager()
        self.llm = get_standard_llm()  # Now using Haiku 4.5 (12x cheaper!)
        self.tier = LLMTier.STANDARD

    async def send_message(self, user_id: int, session_id: int, message: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Send message to Journal Branch.

        Process:
        1. Verify session exists and is journal type
        2. Add user message
        3. Analyze if message is a journal entry (LLM + Heuristic Fallback)
        4. If entry: Extract structured data (mood, tags, themes)
        5. Store entry in UserProfile.data['journal_entries']
        6. Generate empathetic response
        7. Return response
        """
        # Get session
        session = await self.session_manager.get_session(session_id, db)

        if not session or session.user_id != user_id:
            raise ValueError("Session not found")

        if session.session_type != "journal":
            raise ValueError("Not a journal session")

        # Add user message
        await self.session_manager.add_message(session_id, "user", message, {}, db)

        # Analyze message - is this a journal entry?
        is_entry, structured_data = await self._analyze_message(message)

        if is_entry:
            # Store journal entry
            entry_id = await self._store_journal_entry(user_id, message, structured_data, db)

            # Generate empathetic response
            response_text = await self._generate_entry_response(message, structured_data)

            # Add assistant response
            await self.session_manager.add_message(
                session_id, "assistant", response_text, {"entry_created": True, "entry_id": entry_id}, db
            )

            # Trigger embedding population
            await self._trigger_embedding_creation(user_id, entry_id)

            return {
                "session_id": session_id,
                "message": response_text,
                "metadata": {
                    "entry_created": True,
                    "entry_id": entry_id,
                    "mood_score": structured_data.get("mood_score"),
                    "energy_score": structured_data.get("energy_score"),
                },
            }

        else:
            # Regular conversational response
            response_text = await self._generate_conversational_response(message)

            await self.session_manager.add_message(session_id, "assistant", response_text, {}, db)

            return {"session_id": session_id, "message": response_text, "metadata": {"entry_created": False}}

    async def _analyze_message(self, message: str) -> tuple[bool, Optional[Dict]]:
        """
        Analyze if message is a journal entry and extract structured data.

        Returns:
            (is_entry, structured_data)
        """
        prompt = f"""Analyze this message and determine if it's a journal entry.

Message: "{message}"

If it's a journal entry (describing emotions, events, thoughts):
- Extract mood score (1-10, where 1=terrible, 10=amazing)
- Extract energy score (1-10)
- Extract tags (keywords like "anxiety", "happy", "tired")
- Extract themes (categories like "work", "health", "relationships")

Respond with JSON:
{{
    "is_entry": true/false,
    "mood_score": 1-10,
    "energy_score": 1-10,
    "tags": ["tag1", "tag2"],
    "themes": ["theme1", "theme2"]
}}

If NOT a journal entry (question, request), set is_entry to false."""

        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="You are an expert at analyzing journal entries. Respond only with JSON."),
                    HumanMessage(content=prompt),
                ]
            )

            # Parse response
            content = response.content if isinstance(response.content, str) else str(response.content)

            # Try to find JSON in content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)
                return data.get("is_entry", False), data if data.get("is_entry", False) else None

            return False, None

        except Exception:
            # FALLBACK: Heuristic analysis
            # If message is > 20 words and contains emotion words, assume entry
            word_count = len(message.split())
            emotion_words = ["feel", "felt", "feeling", "anxious", "happy", "sad", "tired", "excited", "angry", "mood"]
            has_emotion = any(word in message.lower() for word in emotion_words)

            if word_count > 10 and (has_emotion or word_count > 30):
                # Default entry with neutral scores
                return True, {"mood_score": 5, "energy_score": 5, "tags": [], "themes": []}

            # Not a journal entry
            return False, None

    async def _store_journal_entry(self, user_id: int, text: str, structured_data: Dict, db: AsyncSession) -> str:
        """Store journal entry in UserProfile.data['journal_entries']."""
        # Get profile
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one()

        # Inject Magi chronos context
        context_snapshot = {}
        try:
            from src.app.core.state.chronos import get_chronos_manager
            chronos_manager = get_chronos_manager()
            chronos_state = await chronos_manager.get_user_chronos(user_id)
            
            if chronos_state:
                context_snapshot["magi"] = {
                    "period_card": chronos_state.get("current_card", {}).get("name"),
                    "period_day": 52 - (chronos_state.get("days_remaining", 0) or 0),
                    "period_total": 52,
                    "planetary_ruler": chronos_state.get("current_planet"),
                    "theme": chronos_state.get("theme"),
                    "guidance": chronos_state.get("guidance"),
                    "period_start": chronos_state.get("period_start"),
                    "period_end": chronos_state.get("period_end"),
                    "progress_percent": round(
                        ((52 - (chronos_state.get("days_remaining", 0) or 0)) / 52) * 100, 2
                    ),
                }
        except Exception as e:
            print(f"[JournalChat] Failed to inject magi context: {e}")

        # Create entry
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "timestamp": datetime.now(dt_timezone.utc).isoformat(),
            "text": text,
            "mood_score": structured_data.get("mood_score", 5),
            "energy_score": structured_data.get("energy_score", 5),
            "tags": structured_data.get("tags", []),
            "themes": structured_data.get("themes", []),
            "context_snapshot": context_snapshot,
        }

        # Add to journal_entries
        # We need to deep copy the existing data, modify it, and reassign to trigger SQLAlchemy detection
        data = dict(profile.data)
        if "journal_entries" not in data:
            data["journal_entries"] = []

        data["journal_entries"].append(entry)
        profile.data = data

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(profile, "data")

        await db.commit()

        return entry_id

    async def _generate_entry_response(self, text: str, structured: Dict) -> str:
        """Generate empathetic response to journal entry."""
        mood = structured.get("mood_score", 5)
        energy = structured.get("energy_score", 5)

        prompt = f"""Generate an empathetic, brief response (2-3 sentences) to this journal entry:

"{text}"

Detected mood: {mood}/10, energy: {energy}/10

Acknowledge their feelings, be supportive. Don't give advice unless they ask."""

        try:
            response = await self.llm.ainvoke(
                [SystemMessage(content="You are a compassionate journaling companion."), HumanMessage(content=prompt)]
            )
            return response.content.strip() if hasattr(response, "content") else str(response).strip()
        except:
            return "Thank you for sharing that. I've recorded it in your journal."

    async def _generate_conversational_response(self, message: str) -> str:
        """Generate response to non-entry message."""
        prompt = f"""Respond to this message in a journaling context:

"{message}"

Be helpful and encourage them to share their thoughts."""

        try:
            response = await self.llm.ainvoke(
                [SystemMessage(content="You are a helpful journaling assistant."), HumanMessage(content=prompt)]
            )
            return response.content.strip() if hasattr(response, "content") else str(response).strip()
        except:
            return "I'm here to help you journal. What's on your mind?"

    async def _trigger_embedding_creation(self, user_id: int, entry_id: str):
        """Trigger vector embedding creation for new entry."""
        # Publish event
        from src.app.core.events.bus import get_event_bus

        try:
            event_bus = get_event_bus()
            # Wait for initialization if needed (though usually done at startup)
            if not getattr(event_bus, "initialized", False):
                await event_bus.initialize()

            await event_bus.publish(
                "journal.entry.created",
                {"user_id": user_id, "entry_id": entry_id, "title": "Journal Entry"},
                source="journal.chat",
                user_id=str(user_id),
            )
        except Exception:
            # Don't fail the request if event publishing fails, but log it
            # In a real app we'd use a logger here
            pass
