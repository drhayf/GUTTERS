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
        self,
        user_id: int,
        message: str,
        db: AsyncSession,
        session_id: Optional[int] = None,
        model_tier: str = "standard",  # Added model_tier (standard/premium)
    ) -> Dict[str, Any]:
        """
        Send message to Master Chat with multi-conversation support.

        Args:
            user_id: User
            message: Content
            db: Database
            session_id: Optional specific conversation ID
            model_tier: 'standard' (Haiku) or 'premium' (Sonnet)
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

        # Configure QueryEngine based on Tier
        # Ideally QueryEngine takes overrides, or we set it here.
        # Check if query_engine has a method to set model, or if we need to pass it to answer_query
        # For now, we'll assume answer_query handles basic logic, but let's see if we can swap the LLM.

        # If the user requested a specific tier, we might need to adjust the engine.
        # But `self.query_engine` was initialized with Premium in __init__.
        # We should probably pass `model_tier` to `answer_query` if supported, or re-init a temp engine.
        # Since QueryEngine is stateful (memory), re-init is cheap if we share memory.

        target_tier = LLMTier.PREMIUM if model_tier == "premium" else LLMTier.STANDARD
        if self.query_engine.tier != target_tier:
            # Create temp engine for this request
            from src.app.core.llm.config import get_premium_llm, get_standard_llm

            llm = get_premium_llm() if target_tier == LLMTier.PREMIUM else get_standard_llm()
            # We need to make sure we don't lose the memory reference
            query_engine_run = QueryEngine(llm, self.query_engine.memory, tier=target_tier, enable_generative_ui=True)
        else:
            query_engine_run = self.query_engine

        # Generate response using Query Engine
        response = await query_engine_run.answer_query(user_id, message, db, use_vector_search=True)

        # Prepare trace for storage
        trace_data = None
        if response.trace:
            trace_data = self._compress_trace_for_storage(response.trace)

        # Prepare component data
        component_data = None
        if response.component:
            component_data = response.component.model_dump(mode="json")

        # INJECT QUEST COMPONENT IF CREATED
        # If the tool 'create_quest' was used, we want to render the Quest Card.
        if not component_data and response.trace and response.trace.tools_used:
            import json
            from src.app.modules.features.quests.models import Quest
            from sqlalchemy import select

            for tool in response.trace.tools_used:
                if tool.tool == "create_quest":
                    # Try to parse the result summary for JSON
                    try:
                        # The tool returns JSON string in our new implementation
                        # But it might be wrapped in text or the LLM might have summarized it?
                        # Wait, the tool definition returns the string. Trace records the result.
                        # If the tool executed successfully, result_summary should be the JSON.
                        # Let's try to find the dict.

                        # Note: `result_summary` in trace might be truncated or processed.
                        # But typically it's the string returned by tool.
                        # We'll look for the substring `{"status":` or similar if it's mixed with text?
                        # Actually our tool returns *only* json.

                        # Remove any potential markdown code blocks
                        clean_json = tool.result_summary.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_json)

                        if data.get("status") == "success" and "quest_id" in data:
                            quest_id = data["quest_id"]

                            # Fetch the full quest object to render
                            stmt = select(Quest).where(Quest.id == quest_id)
                            q_result = await db.execute(stmt)
                            quest = q_result.scalar_one_or_none()

                            if quest:
                                # Create a synthetic component payload
                                component_data = {
                                    "component_id": f"quest_{quest.id}",
                                    "component_type": "QUEST_ITEM",  # Client logic needs to handle this
                                    "title": "Quest Created",
                                    "data": {
                                        # Serialization of Quest.
                                        # We can't just dump the object. Need minimal schema.
                                        "id": quest.id,
                                        "title": quest.title,
                                        "description": quest.description,
                                        "xp_reward": quest.xp_reward,
                                        "recurrence": quest.recurrence.value
                                        if hasattr(quest.recurrence, "value")
                                        else quest.recurrence,
                                        "difficulty": quest.difficulty.value
                                        if hasattr(quest.difficulty, "value")
                                        else quest.difficulty,
                                        "category": quest.category.value
                                        if hasattr(quest.category, "value")
                                        else quest.category,
                                        "is_active": quest.is_active,
                                        "source": "agent",
                                    },
                                }
                                break  # Only show one quest per message for now
                    except Exception as e:
                        # JSON parse error or DB error, ignore component injection
                        # logger.warning(f"Failed to inject quest component: {e}")
                        pass

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
                "model_tier": model_tier,  # Track which model was used
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

    async def get_conversation_history(
        self, user_id: int, limit: int, db: AsyncSession, session_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get Master Chat history."""
        if session_id:
            session = await self.session_manager.get_session(session_id, db)
            if not session or session.user_id != user_id:
                raise ValueError("Invalid session")
        else:
            session = await self.session_manager.get_default_master_conversation(user_id, db)

        messages = await self.session_manager.get_session_history(session.id, db, limit)

        # Hydrate components with user responses
        # This ensures the UI knows if a component has been answered
        from src.app.models.user_profile import UserProfile
        from sqlalchemy import select

        try:
            profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
            profile = profile_result.scalar_one_or_none()

            response_map = {}
            if profile and "component_responses" in profile.data:
                for resp in profile.data["component_responses"]:
                    response_map[resp.get("component_id")] = resp

            hydrated_messages = []
            for msg in messages:
                msg_dict = {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "metadata": msg.meta,
                }

                # Check if this message has a component and if we have a response for it
                if msg.meta and msg.meta.get("component"):
                    comp_data = msg.meta["component"]
                    comp_id = comp_data.get("component_id")

                    if comp_id:
                        # Robust matching: Strip whitespace and ensure string type
                        clean_comp_id = str(comp_id).strip()

                        # Try exact match first, then clean match
                        if clean_comp_id in response_map:
                            # Create a copy of metadata to avoid mutating the DB object if it's attached
                            new_meta = msg.meta.copy()
                            # Ensure deep copy of component dict to modify it safely
                            new_meta["component"] = comp_data.copy()
                            new_meta["component"]["response"] = response_map[clean_comp_id]
                            msg_dict["metadata"] = new_meta
                        else:
                            # Fallback check for case sensitivity
                            # (This is O(N) but map is small per user profile)
                            found_resp = None
                            for key, val in response_map.items():
                                if str(key).strip() == clean_comp_id:
                                    found_resp = val
                                    break

                            if found_resp:
                                new_meta = msg.meta.copy()
                                new_meta["component"] = comp_data.copy()
                                new_meta["component"]["response"] = found_resp
                                msg_dict["metadata"] = new_meta

                hydrated_messages.append(msg_dict)

            return hydrated_messages

        except Exception as e:
            # Fallback if profile fetch fails
            print(f"Error hydrating chat history: {e}")
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
