from collections.abc import Callable, Generator, AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from datetime import datetime, timezone as dt_timezone

from src.app.core.config import settings
from src.app.main import app
from src.app.core.db.database import async_engine, local_session as async_session_maker, Base

# CRITICAL: Import all models to register with SQLAlchemy registry
# This must happen BEFORE any database operations
from src.app.models.user import User
from src.app.models.user_profile import UserProfile
from src.app.models.embedding import Embedding
from src.app.models.chat_session import ChatSession, ChatMessage
from src.app.core.security import get_password_hash
from sqlalchemy import select, delete
from tests.fixtures.seed_data import SeedDataGenerator


def configure_mappers():
    """
    Explicitly configure all SQLAlchemy mappers.

    This resolves circular dependencies by ensuring all models
    are registered before any database operations.
    """
    try:
        # This triggers mapper compilation for all models
        Base.registry.configure()
    except Exception as e:
        # If already configured, ignore
        pass


# Call at module load time (before any tests)
configure_mappers()

DATABASE_URI = settings.POSTGRES_URI
DATABASE_PREFIX = settings.POSTGRES_SYNC_PREFIX

sync_engine = create_engine(DATABASE_PREFIX + DATABASE_URI)
sync_session_maker = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


fake = Faker()


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, Any, None]:
    with TestClient(app) as _client:
        yield _client
    app.dependency_overrides = {}
    sync_engine.dispose()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, Any]:
    """Async database session fixture."""
    async with async_session_maker() as session:
        yield session
    # Cleanup after test if needed, or rely on transaction/rollback if using that pattern
    # For high fidelity, we might want to clean up seeded data, but usually we use a test DB.


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_state():
    """Reset state between tests."""
    yield
    # We do NOT nullify singletons or dispose engine here
    # as it breaks async connection pool and event loops.
    pass


@pytest_asyncio.fixture
async def memory():
    """Get ActiveMemory instance with real Redis connection and clean slate."""
    from src.app.core.memory.active_memory import get_active_memory

    mem = get_active_memory()
    await mem.initialize()

    # Initialize EventBus too as it shares Redis
    from src.app.core.events.bus import get_event_bus

    bus = get_event_bus()
    await bus.initialize()

    # FLUSH REDIS to ensure clean slate
    if mem.redis_client:
        await mem.redis_client.flushdb()

    return mem


@pytest.fixture
def sync_db() -> Generator[Session, Any, None]:
    """Synchronous database session fixture."""
    session = sync_session_maker()
    yield session
    session.close()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    # Check if exists
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            name="Test User",
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


def override_dependency(dependency: Callable[..., Any], mocked_response: Any) -> None:
    app.dependency_overrides[dependency] = lambda: mocked_response


@pytest.fixture
def mock_db():
    """Mock database session for unit tests."""
    return Mock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    """Mock Redis connection for unit tests."""
    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def sample_user_data():
    """Generate sample user data for tests."""
    return {
        "name": fake.name(),
        "username": fake.user_name(),
        "email": fake.email(),
        "password": fake.password(),
    }


@pytest.fixture
def sample_user_read():
    """Generate a sample UserRead object."""
    from uuid6 import uuid7

    from src.app.schemas.user import UserRead

    return UserRead(
        id=1,
        uuid=uuid7(),
        name=fake.name(),
        username=fake.user_name(),
        email=fake.email(),
        profile_image_url=fake.image_url(),
        is_superuser=False,
        created_at=fake.date_time(),
        updated_at=fake.date_time(),
        tier_id=None,
    )


@pytest.fixture
def current_user_dict():
    """Mock current user from auth dependency."""
    return {
        "id": 1,
        "username": fake.user_name(),
        "email": fake.email(),
        "name": fake.name(),
        "is_superuser": False,
    }


@pytest_asyncio.fixture
async def seeded_user(test_user):
    """
    Extend test_user with fully seeded data for intelligence module testing.

    Seeds:
    - Journal entries (60 days, 3/week, with detectable patterns)
    - Observer findings (5 patterns)
    - Tracking history (60 days of solar/lunar/transit data)

    This allows testing Enhanced Synthesis, Hypothesis, and Vector Search
    WITHOUT building Journal Module first.
    """
    test_user_id = test_user.id
    async with async_session_maker() as db:
        # Get user profile
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user_id))
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=test_user_id, data={})
            db.add(profile)
            await db.flush()

        # Seed journal entries
        profile.data["journal_entries"] = SeedDataGenerator.generate_journal_entries(
            test_user_id, days=60, entries_per_week=3
        )

        # Seed observer findings
        profile.data["observer_findings"] = SeedDataGenerator.generate_observer_findings(test_user_id)

        # Seed tracking history
        profile.data["tracking_history"] = SeedDataGenerator.generate_tracking_history(test_user_id, days=60)

        # Mark data as modified for PostgreSQL
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(profile, "data")

        await db.commit()
        # db.expunge_all() is handled by the async session maker context manager usually,
        # but I'll add refresh/expunge if needed for safety.

    yield test_user_id

    # Cleanup seeded data after test
    async with async_session_maker() as db:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user_id))
        profile = result.scalar_one_or_none()


@pytest_asyncio.fixture
async def clean_redis():
    """Clean Redis before test."""
    from src.app.core.memory import get_active_memory

    memory = get_active_memory()
    await memory.initialize()

    # Clear all keys (development only!)
    if memory.redis_client:
        await memory.redis_client.flushdb()

    yield

    # Cleanup
    if memory.redis_client:
        await memory.redis_client.flushdb()
