"""
GUTTERS State Tracker

Tracks profile completion state for dashboard and observability.
Calculates completion percentage and data coverage.

Example:
    >>> from src.app.core.state.tracker import get_state_tracker
    >>> tracker = get_state_tracker()
    >>> state = await tracker.get_profile_state(user_id=123)
    >>> print(f"Profile {state['completion_percentage']:.1f}% complete")
"""

from datetime import datetime, UTC, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...crud.crud_user_profile import crud_user_profiles


# Domain configuration for completion tracking
PROFILE_DOMAINS = {
    "natal_chart": {
        "required_fields": ["planets", "houses", "ascendant"],
        "weight": 1.0,  # Primary domain
    },
    "human_design": {
        "required_fields": ["type", "strategy", "authority", "profile"],
        "weight": 0.8,
    },
    "numerology": {
        "required_fields": ["life_path", "expression", "soul_urge"],
        "weight": 0.6,
    },
    "vedic_astrology": {
        "required_fields": ["lagna", "nakshatras", "dashas"],
        "weight": 0.7,
    },
    "gene_keys": {
        "required_fields": ["profile", "sequences"],
        "weight": 0.5,
    },
    "chinese_astrology": {
        "required_fields": ["animal", "element", "pillars"],
        "weight": 0.5,
    },
    "mayan_calendar": {
        "required_fields": ["kin", "tone", "glyph"],
        "weight": 0.4,
    },
    "enneagram": {
        "required_fields": ["type", "wing", "instinct"],
        "weight": 0.5,
    },
    "kabbalah": {
        "required_fields": ["tree_positions", "paths"],
        "weight": 0.4,
    },
    "name_analysis": {
        "required_fields": ["letters", "values"],
        "weight": 0.3,
    },
    "synthesis": {
        "required_fields": ["synthesis", "modules_included"],
        "weight": 0.8,  # High importance - synthesis shows integration
    },
    "hypothesis": {
        "required_fields": ["confirmed_hypotheses"],
        "weight": 0.5,
    },
    "progression": {
        "required_fields": ["level", "rank", "sync_rate"],
        "weight": 0.6,
    },
}


class StateTracker:
    """
    Tracks profile completion state for observability.

    Provides completion metrics and domain coverage.
    """

    async def get_profile_state(self, user_id: int) -> dict[str, Any]:
        """
        Get comprehensive profile state for a user.

        Args:
            user_id: User ID to get state for

        Returns:
            {
                "completion_percentage": float (0-100),
                "domains": {
                    "natal_chart": {"complete": bool, "confidence": float},
                    "human_design": {"complete": bool, "confidence": float},
                    ...
                },
                "last_synthesis": datetime | None,
                "total_data_points": int
            }
        """
        async for db in async_get_db():
            # Get user profile
            profile = await crud_user_profiles.get(db=db, user_id=user_id)

            if profile is None:
                return {
                    "completion_percentage": 0.0,
                    "domains": {name: {"complete": False, "confidence": 0.0} for name in PROFILE_DOMAINS},
                    "last_synthesis": None,
                    "total_data_points": 0,
                }

            # Get profile data
            profile_data = profile.get("data", {}) if isinstance(profile, dict) else getattr(profile, "data", {}) or {}

            # Analyze domains
            domains = {}
            total_weight = 0.0
            completed_weight = 0.0
            total_data_points = 0

            for domain_name, config in PROFILE_DOMAINS.items():
                domain_data = profile_data.get(domain_name, {})
                required = config["required_fields"]
                weight = config["weight"]

                # Count filled fields
                filled = 0
                for field in required:
                    if domain_data.get(field) is not None:
                        filled += 1
                        total_data_points += 1

                # Calculate confidence (0-1)
                confidence = filled / len(required) if required else 0.0
                complete = confidence >= 0.8  # 80% threshold for "complete"

                domains[domain_name] = {
                    "complete": complete,
                    "confidence": round(confidence, 2),
                    "filled_fields": filled,
                    "total_fields": len(required),
                }

                total_weight += weight
                if complete:
                    completed_weight += weight

            # Calculate overall completion
            completion_percentage = (completed_weight / total_weight * 100) if total_weight > 0 else 0.0

            # Get last synthesis time
            last_synthesis = (
                profile.get("updated_at") if isinstance(profile, dict) else getattr(profile, "updated_at", None)
            )

            return {
                "completion_percentage": round(completion_percentage, 1),
                "domains": domains,
                "last_synthesis": last_synthesis,
                "total_data_points": total_data_points,
            }

    async def get_domain_summary(self, user_id: int) -> dict[str, str]:
        """
        Get a simple summary of domain completion status.

        Args:
            user_id: User ID

        Returns:
            {"natal_chart": "complete", "human_design": "partial", ...}
        """
        state = await self.get_profile_state(user_id)

        summary = {}
        for domain, info in state["domains"].items():
            if info["complete"]:
                summary[domain] = "complete"
            elif info["confidence"] > 0:
                summary[domain] = "partial"
            else:
                summary[domain] = "missing"

        return summary

    # =========================================================================
    # Genesis Integration
    # =========================================================================

    async def update_genesis_status(self, user_id: int, hypothesis_count: int, fields_uncertain: list[str]) -> None:
        """
        Update profile state when Genesis creates hypotheses.

        Stores genesis status in profile for dashboard visibility.
        """
        async for db in async_get_db():
            profile = await crud_user_profiles.get(db=db, user_id=user_id)
            if not profile:
                return

            # Update genesis data in profile
            profile_data = getattr(profile, "data", {}) or {}
            profile_data["genesis"] = {
                "active": True,
                "hypothesis_count": hypothesis_count,
                "fields_uncertain": fields_uncertain,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "confirmations": {},
            }

            # Save
            await crud_user_profiles.update(db=db, object={"data": profile_data}, user_id=user_id)
            break

    async def update_field_confirmed(self, user_id: int, field: str, confirmed_value: str) -> None:
        """
        Update profile state when a field is confirmed via Genesis.
        """
        async for db in async_get_db():
            profile = await crud_user_profiles.get(db=db, user_id=user_id)
            if not profile:
                return

            profile_data = getattr(profile, "data", {}) or {}

            # Update genesis confirmations
            if "genesis" not in profile_data:
                profile_data["genesis"] = {"confirmations": {}, "fields_uncertain": []}

            profile_data["genesis"]["confirmations"][field] = {
                "value": confirmed_value,
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
            }

            # Remove from uncertain fields
            if field in profile_data["genesis"].get("fields_uncertain", []):
                profile_data["genesis"]["fields_uncertain"].remove(field)

            # Check if all fields confirmed
            if not profile_data["genesis"].get("fields_uncertain"):
                profile_data["genesis"]["active"] = False
                profile_data["genesis"]["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Save
            await crud_user_profiles.update(db=db, object={"data": profile_data}, user_id=user_id)
            break

    async def get_genesis_status(self, user_id: int) -> dict[str, Any] | None:
        """Get current Genesis status for a user."""
        async for db in async_get_db():
            profile = await crud_user_profiles.get(db=db, user_id=user_id)
            if not profile:
                return None

            profile_data = getattr(profile, "data", {}) or {}
            return profile_data.get("genesis")

    async def update_synthesis_status(self, user_id: int, db: AsyncSession) -> None:
        """Update synthesis completion status."""
        from src.app.core.memory.active_memory import get_active_memory

        memory = get_active_memory()
        await memory.initialize()

        synthesis = await memory.get_master_synthesis(user_id)

        if synthesis and synthesis.get("modules_included"):
            # Synthesis complete
            await self.mark_domain_complete(user_id, "synthesis", db)
        else:
            # Incomplete
            await self.mark_domain_incomplete(user_id, "synthesis", db)

    async def update_hypothesis_status(self, user_id: int, db: AsyncSession) -> None:
        """Update hypothesis completion status."""
        from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage

        storage = HypothesisStorage()
        confirmed = await storage.get_confirmed_hypotheses(user_id)

        if len(confirmed) >= 3:  # At least 3 confirmed hypotheses
            await self.mark_domain_complete(user_id, "hypothesis", db)
        else:
            await self.mark_domain_incomplete(user_id, "hypothesis", db)

    async def mark_domain_complete(self, user_id: int, domain: str, db: AsyncSession) -> None:
        """Mark a domain as complete in the user profile."""
        profile = await crud_user_profiles.get(db=db, user_id=user_id)
        if not profile:
            return

        profile_data = getattr(profile, "data", {}) or {}
        if "domains_complete" not in profile_data:
            profile_data["domains_complete"] = {}

        profile_data["domains_complete"][domain] = True

        await crud_user_profiles.update(db=db, object={"data": profile_data}, user_id=user_id)

    async def mark_domain_incomplete(self, user_id: int, domain: str, db: AsyncSession) -> None:
        """Mark a domain as incomplete in the user profile."""
        profile = await crud_user_profiles.get(db=db, user_id=user_id)
        if not profile:
            return

        profile_data = getattr(profile, "data", {}) or {}
        if "domains_complete" not in profile_data:
            return

        if domain in profile_data["domains_complete"]:
            profile_data["domains_complete"][domain] = False

            await crud_user_profiles.update(db=db, object={"data": profile_data}, user_id=user_id)


# Singleton instance
_state_tracker: StateTracker | None = None


def get_state_tracker() -> StateTracker:
    """
    Get the singleton StateTracker instance.

    Returns:
        Global StateTracker instance

    Example:
        >>> tracker = get_state_tracker()
        >>> state = await tracker.get_profile_state(123)
    """
    global _state_tracker
    if _state_tracker is None:
        _state_tracker = StateTracker()
    return _state_tracker
