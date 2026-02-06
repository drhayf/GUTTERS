
from datetime import datetime

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.pool import NullPool

from src.app.core.db.database import DATABASE_URL, Base, local_session
from src.app.core.memory import get_active_memory
from src.app.models.user import User
from src.app.models.user_profile import UserProfile


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Ensure database tables exist."""

    from sqlalchemy.ext.asyncio import create_async_engine

    # Use a temporary engine for schema setup
    temp_engine = create_async_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={
            "statement_cache_size": 0,
            "server_settings": {"jit": "off"}
        }
    )

    async with temp_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await temp_engine.dispose()
    yield

@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_state():
    """Clear singletons and dispose of the global engine after each test."""
    yield

    # Dispose engine
    from src.app.core.db.database import async_engine
    await async_engine.dispose()

    # Clear memory singletons
    import src.app.core.memory.active_memory as active_memory
    import src.app.core.memory.synthesis_orchestrator as synthesis_orchestrator

    active_memory._active_memory = None
    synthesis_orchestrator._orchestrator = None

@pytest_asyncio.fixture
async def memory():
    """Get ActiveMemory instance with real Redis connection."""
    mem = get_active_memory()
    await mem.initialize()
    if mem.redis_client:
        await mem.redis_client.flushdb()
    return mem

@pytest_asyncio.fixture
async def test_user_id():
    """Get or create test user for integration tests."""
    user_id = None
    async with local_session() as db:
        # Clean start: Delete if exists
        await db.execute(
            select(User).where(User.email == "test_tracking_int@example.com")
        )
        # Note: Delete using delete() statement is better but let's just use what we have or pure SQL?
        # Using sqlalchemy delete
        from sqlalchemy import delete
        await db.execute(
            delete(User).where(User.email == "test_tracking_int@example.com")
        )
        await db.commit()

        # Create fresh user
        user = User(
            name="Tracking Test User",
            username="test_tracking_int",
            email="test_tracking_int@example.com",
            hashed_password="hashed_password",
            birth_date=datetime(1990, 1, 1).date(),
            birth_time=datetime(1990, 1, 1, 12, 0).time(),
            birth_location="London, UK",
            birth_latitude=51.5074,
            birth_longitude=-0.1278
        )
        db.add(user)
        await db.commit()

        # Get ID via scalar select
        result = await db.execute(
            select(User.id).where(User.email == "test_tracking_int@example.com")
        )
        user_id = result.scalar_one()

        # Create profile
        profile = UserProfile(user_id=user_id, data={})
        db.add(profile)
        await db.commit()

        db.expunge_all()

    yield user_id

