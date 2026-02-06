"""
Chat session management.

Handles creation, retrieval, and management of Master + Branch sessions.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.chat_session import ChatMessage, ChatSession, SessionType


class SessionManager:
    """Manage chat sessions for users."""

    async def get_or_create_master_session(self, user_id: int, db: AsyncSession) -> ChatSession:
        """
        Get or create Master Chat session.

        Each user has exactly one Master Chat session.
        """
        # Check if exists
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.session_type == SessionType.MASTER.value)
            .order_by(ChatSession.created_at.desc())
        )
        session = result.scalars().first()

        if session:
            return session

        # Create new Master Chat session
        session = ChatSession(
            user_id=user_id,
            session_type=SessionType.MASTER.value,
            name="Master Chat",
            contribute_to_memory=True,  # Master always contributes
            meta={},
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    async def create_branch_session(
        self, user_id: int, session_type: str, name: str, contribute_to_memory: bool, db: AsyncSession
    ) -> ChatSession:
        """
        Create a branch session (Journal, Nutrition, etc.).

        Args:
            user_id: User ID
            session_type: 'journal', 'nutrition', etc.
            name: Display name for session
            contribute_to_memory: Whether to feed into synthesis
        """
        session = ChatSession(
            user_id=user_id,
            session_type=session_type,
            name=name,
            contribute_to_memory=contribute_to_memory,
            meta={},
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    async def get_session(self, session_id: int, db: AsyncSession) -> Optional[ChatSession]:
        """Get session by ID."""
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self, user_id: int, db: AsyncSession, session_type: Optional[str] = None
    ) -> List[ChatSession]:
        """Get all sessions for user, optionally filtered by type."""
        query = select(ChatSession).options(selectinload(ChatSession.messages)).where(ChatSession.user_id == user_id)

        if session_type:
            query = query.where(ChatSession.session_type == session_type)

        query = query.order_by(ChatSession.updated_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self, session_id: int, role: str, content: str, metadata: dict, db: AsyncSession
    ) -> ChatMessage:
        """Add message to session."""
        message = ChatMessage(session_id=session_id, role=role, content=content, meta=metadata)
        db.add(message)

        # Update session updated_at
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one()
        session.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(message)

        return message

    async def get_session_history(self, session_id: int, db: AsyncSession, limit: int = 50) -> List[ChatMessage]:
        """Get conversation history for session."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Oldest first

    async def toggle_memory_contribution(self, session_id: int, contribute: bool, db: AsyncSession) -> ChatSession:
        """Toggle whether session contributes to synthesis."""
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one()

        # Can't disable Master Chat contribution
        if session.session_type == SessionType.MASTER.value:
            raise ValueError("Master Chat always contributes to memory")

        session.contribute_to_memory = contribute
        await db.commit()
        await db.refresh(session)

        return session
        return session

    async def create_master_conversation(self, user_id: int, conversation_name: str, db: AsyncSession) -> ChatSession:
        """
        Create a new Master Chat conversation.

        Unlike branches, these are full Master Chats with different names.

        Args:
            user_id: User ID
            conversation_name: Name for conversation (e.g., "Work Planning")
            db: Database session

        Returns:
            New ChatSession with session_type='master'
        """
        session = ChatSession(
            user_id=user_id,
            session_type=SessionType.MASTER.value,
            name=conversation_name,
            conversation_name=conversation_name,  # Both fields for clarity
            contribute_to_memory=True,  # Master chats always contribute
            meta={},
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    async def get_master_conversations(
        self, user_id: int, db: AsyncSession, include_archived: bool = False
    ) -> List[ChatSession]:
        """
        Get all Master Chat conversations for user.

        Args:
            user_id: User ID
            include_archived: Include archived conversations
            db: Database session

        Returns:
            List of master conversations, sorted by updated_at desc
        """
        query = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.user_id == user_id, ChatSession.session_type == SessionType.MASTER.value)
        )

        if not include_archived:
            # Filter out archived (check if key doesn't exist or is not true)
            # Using astext casting for JSONB value comparison
            query = query.where(
                or_(ChatSession.meta["is_archived"].astext.is_(None), ChatSession.meta["is_archived"].astext != "true")
            )

        query = query.order_by(ChatSession.updated_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_default_master_conversation(self, user_id: int, db: AsyncSession) -> ChatSession:
        """
        Get or create the default Master Chat conversation.

        This is the conversation created on first use, named "General".

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Default master conversation
        """
        # Look for conversation named "General" or "Master Chat"
        # Also include NULL conversation_name for legacy sessions
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.session_type == SessionType.MASTER.value,
                or_(
                    ChatSession.conversation_name == "General",
                    ChatSession.conversation_name == "Master Chat",
                    ChatSession.conversation_name.is_(None),
                ),
                # Exclude archived from being 'default' unless it's the only one?
                # Better to just ignore archived status for retrieval by specific name criteria
            )
            .order_by(ChatSession.created_at.asc())  # Oldest first
        )

        session = result.scalars().first()

        if session:
            # If found legacy session without name, update it
            if not session.conversation_name:
                session.conversation_name = "General"
                session.name = "General"
                await db.commit()
                await db.refresh(session)
            return session

        # No default exists, create it
        return await self.create_master_conversation(user_id, "General", db)

    async def archive_conversation(self, session_id: int, db: AsyncSession) -> ChatSession:
        """
        Archive a conversation.

        Archived conversations are hidden from default list but not deleted.

        Args:
            session_id: Session to archive
            db: Database session

        Returns:
            Updated session
        """
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one()

        # Add archived flag to metadata
        # Ensure meta is a dict
        if session.meta is None:
            session.meta = {}

        # Create a copy to trigger update (SQLAlchemy JSONB tracking)
        new_meta = session.meta.copy()
        new_meta["is_archived"] = True
        new_meta["archived_at"] = datetime.now(UTC).isoformat()
        session.meta = new_meta

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(session, "meta")

        await db.commit()
        await db.refresh(session)

        return session

    async def delete_conversation(self, session_id: int, user_id: int, db: AsyncSession) -> bool:
        """
        Delete a conversation permanently.

        Cascade deletes all messages.

        Args:
            session_id: Session to delete
            user_id: User ID (for verification)
            db: Database session

        Returns:
            True if deleted
        """
        # Verify ownership
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError("Session not found or access denied")

        # Can't delete if it's the only master conversation
        # Only check active ones to prevent deleting the last active one
        master_count = await db.execute(
            select(func.count(ChatSession.id)).where(
                ChatSession.user_id == user_id,
                ChatSession.session_type == SessionType.MASTER.value,
                # Using astext casting for JSONB value comparison
                or_(ChatSession.meta["is_archived"].astext.is_(None), ChatSession.meta["is_archived"].astext != "true"),
            )
        )
        count = master_count.scalar() or 0

        # If this is a master session and it's the last one (or only one), prevent delete
        if session.session_type == SessionType.MASTER.value and count <= 1:
            # Check if this session is indeed one of the counted ones (not archived)
            is_archived = session.meta and session.meta.get("is_archived") is True
            if not is_archived:
                raise ValueError("Cannot delete the only master conversation")

        # Delete
        await db.execute(delete(ChatSession).where(ChatSession.id == session_id))
        await db.commit()

        return True

    async def search_conversations(
        self, user_id: int, query_str: str, limit: int, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Search across all conversations.

        Args:
            user_id: User ID
            query_str: Search query
            limit: Max results
            db: Database session

        Returns:
            List of matching messages with context
        """
        # Search message content
        result = await db.execute(
            select(ChatMessage, ChatSession)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.user_id == user_id,
                or_(ChatMessage.content.ilike(f"%{query_str}%"), ChatSession.conversation_name.ilike(f"%{query_str}%")),
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )

        results = []
        for message, session in result.all():
            results.append(
                {
                    "message_id": message.id,
                    "session_id": session.id,
                    "conversation_name": session.conversation_name or session.name or "Unknown",
                    "content": message.content,
                    "role": message.role,
                    "created_at": message.created_at.isoformat(),
                    "snippet": message.content[:200] + "..." if len(message.content) > 200 else message.content,
                }
            )

        return results
