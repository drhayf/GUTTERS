"""
Hypothesis persistence.

Stores hypotheses in UserProfile.data['hypotheses'] and caches in Redis.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from src.app.models.user_profile import UserProfile

from .models import Hypothesis


class HypothesisStorage:
    """Store and retrieve theory-based hypotheses."""

    async def store_hypothesis(self, hypothesis: Hypothesis, db: AsyncSession) -> None:
        """Store hypothesis in database and cache in Redis."""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == hypothesis.user_id))
        profile = result.scalar_one_or_none()

        if not profile:
            # Create profile if not exists (should normally exist)
            profile = UserProfile(user_id=hypothesis.user_id, data={})
            db.add(profile)

        if "hypotheses" not in profile.data:
            profile.data["hypotheses"] = []

        # Add or update hypothesis
        existing_index = next((i for i, h in enumerate(profile.data["hypotheses"]) if h["id"] == hypothesis.id), None)

        if existing_index is not None:
            profile.data["hypotheses"][existing_index] = hypothesis.model_dump(mode="json")
        else:
            profile.data["hypotheses"].append(hypothesis.model_dump(mode="json"))

        # Mark as modified for JSONB
        flag_modified(profile, "data")

        await db.commit()

        # Cache in Redis
        from src.app.core.memory.active_memory import get_active_memory

        memory = get_active_memory()
        await memory.initialize()

        # Get all hypotheses to update cache
        await memory.set(
            f"hypotheses:{hypothesis.user_id}",
            profile.data["hypotheses"],
            ttl=604800,  # 7 days
        )

    async def get_hypotheses(
        self, user_id: int, min_confidence: float = 0.0, status: Optional[str] = None
    ) -> List[Hypothesis]:
        """Get theory hypotheses for user."""
        from src.app.core.memory.active_memory import get_active_memory

        memory = get_active_memory()
        await memory.initialize()

        # Try Redis first
        cached = await memory.get(f"hypotheses:{user_id}")

        if cached:
            hypotheses_data = cached
        else:
            # Fallback to database
            from src.app.core.db.database import local_session

            async with local_session() as db:
                result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
                profile = result.scalar_one_or_none()

                if not profile or "hypotheses" not in profile.data:
                    return []

                hypotheses_data = profile.data["hypotheses"]

                # Cache
                await memory.set(f"hypotheses:{user_id}", hypotheses_data, ttl=604800)

        # Parse and filter
        hypotheses = [Hypothesis(**h) for h in hypotheses_data]

        # Filter by confidence
        hypotheses = [h for h in hypotheses if h.confidence >= min_confidence]

        # Filter by status
        if status:
            hypotheses = [h for h in hypotheses if h.status.value == status]

        return hypotheses

    async def get_confirmed_hypotheses(self, user_id: int) -> List[Hypothesis]:
        """Get only confirmed hypotheses (confidence > 0.85)."""
        return await self.get_hypotheses(user_id, min_confidence=0.85, status="confirmed")
