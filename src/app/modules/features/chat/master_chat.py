"""
Master Chat handler.

Main conversational interface with full context.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .session_manager import SessionManager
from src.app.models.chat_session import SessionType
from src.app.modules.intelligence.query.engine import QueryEngine
from src.app.core.llm.config import get_premium_llm, LLMTier


class MasterChatHandler:
    """
    Master Chat handler.

    Uses Claude Sonnet 4.5 for user-facing quality responses.
    """

    def __init__(self, query_engine: Optional[QueryEngine] = None):
        # If no query engine provided, create one with premium tier
        if query_engine is None:
            from src.app.core.memory import get_active_memory

            memory = get_active_memory()
            query_engine = QueryEngine(
                llm=get_premium_llm(),  # Sonnet 4.5
                memory=memory,
                tier=LLMTier.PREMIUM,
            )

        self.query_engine = query_engine
        self.session_manager = SessionManager()

    async def send_message(
        self, user_id: int, message: str, db: AsyncSession, session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send message to Master Chat with multi-conversation support.

        Args:
            user_id: User
            message: Content
            db: Database
            session_id: Optional specific conversation ID
        """
        # Determine session
        if session_id:
            # Use specified conversation
            session = await self.session_manager.get_session(session_id, db)

            if not session or session.user_id != user_id:
                raise ValueError("Invalid session")

            if session.session_type != SessionType.MASTER.value:
                raise ValueError("Not a master conversation")
        else:
            # Use default conversation
            session = await self.session_manager.get_default_master_conversation(user_id, db)

        # Add user message
        await self.session_manager.add_message(session.id, "user", message, {}, db)

        # Get conversation history for context (last 10 messages)
        # This helps the LLM (and components) understand immediate context
        history = await self.session_manager.get_session_history(session.id, db=db, limit=10)
        # Convert to dict format for potentially passing to engine in future if engine supports history
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in history]

        # Generate response using Query Engine
        # Note: QueryEngine typically handles its own history retrieval or is stateless per query
        # Phase 7c added generative_ui support which might use history decisioning
        response = await self.query_engine.answer_query(user_id, message, db, use_vector_search=True)

        # Prepare trace for storage
        trace_data = None
        if response.trace:
            trace_data = self._compress_trace_for_storage(response.trace)

        # Prepare component data
        component_data = None
        if response.component:
            component_data = response.component.model_dump(mode="json")

        # Add assistant response with detailed metadata
        await self.session_manager.add_message(
            session.id,
            "assistant",
            response.answer,
            {
                "modules_consulted": response.modules_consulted,
                "confidence": response.confidence,
                "sources_used": response.sources_used,
                "trace": trace_data,
                "component": component_data,
            },
            db,
        )

        return {
            "session_id": session.id,
            "conversation_name": session.conversation_name or session.name or "Master Chat",
            "message": response.answer,
            "modules_consulted": response.modules_consulted,
            "confidence": response.confidence,
            "trace": trace_data,
            "component": component_data,
        }

    def _compress_trace_for_storage(self, trace) -> Dict[str, Any]:
        """
        Prepare trace for JSONB storage.
        Ensures critical data is kept while preventing extreme bloat.
        """
        # For now, we return full model dump as requested,
        # but with truncation safety on large string fields.
        trace_dict = trace.model_dump(mode="json")

        # Truncate long result summaries in tool calls
        for tool_call in trace_dict.get("tools_used", []):
            if len(tool_call.get("result_summary", "")) > 500:
                tool_call["result_summary"] = tool_call["result_summary"][:497] + "..."

        return trace_dict

    async def get_conversation_history(self, user_id: int, limit: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get Master Chat history."""
        session = await self.session_manager.get_or_create_master_session(user_id, db)
        messages = await self.session_manager.get_session_history(session.id, limit, db)

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "metadata": msg.meta,
            }
            for msg in messages
        ]

    async def get_conversation_list(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get list of all master conversations."""

        conversations = await self.session_manager.get_master_conversations(user_id, include_archived=False, db=db)

        return [
            {
                "id": conv.id,
                "name": conv.conversation_name or conv.name or "Unnamed Conversation",
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages) if conv.messages else 0,
            }
            for conv in conversations
        ]
