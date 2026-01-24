"""
Test for seeded_user fixture.
"""
import pytest
import pytest_asyncio
from sqlalchemy import select
from src.app.models.user_profile import UserProfile
from src.app.core.db.database import local_session as async_session_maker

@pytest.mark.asyncio
async def test_seeded_user(seeded_user):
    """Verify seeded_user fixture populates database correctly."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == seeded_user)
        )
        profile = result.scalar_one()
        
        assert "journal_entries" in profile.data
        assert "observer_findings" in profile.data
        assert "tracking_history" in profile.data
        assert len(profile.data["journal_entries"]) > 20
        assert len(profile.data["observer_findings"]) == 5
