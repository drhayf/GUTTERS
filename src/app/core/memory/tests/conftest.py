import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy import select

from src.app.core.memory import get_active_memory, get_orchestrator, SynthesisTrigger
from src.app.core.db.database import local_session, async_engine, Base, DATABASE_URL
from src.app.modules.registry import ModuleRegistry
from sqlalchemy.pool import NullPool
from src.app.models.user import User
from src.app.models.user_profile import UserProfile

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Ensure database tables exist and register mock modules."""
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # Register mock module for synthesis tests
    class MockModule:
        def __init__(self, name, layer):
            self.name = name
            self.layer = layer
    
    if not ModuleRegistry.get_module("astrology"):
        ModuleRegistry.register(MockModule("astrology", "calculation"))
    
    # Use a temporary engine for schema setup to avoid loop-binding global engine
    temp_engine = create_async_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={
            "statement_cache_size": 0,
            "server_settings": {"jit": "off"}
        }
    )
    
    async with temp_engine.begin() as conn:
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
    import src.app.core.activity.logger as activity_logger
    
    active_memory._active_memory = None
    synthesis_orchestrator._orchestrator = None
    activity_logger._activity_logger = None

@pytest_asyncio.fixture
async def memory():
    """Get ActiveMemory instance with real Redis connection."""
    mem = get_active_memory()
    if not mem.redis_client:
        await mem.initialize()
    return mem

@pytest_asyncio.fixture
async def orchestrator(memory):
    """Get SynthesisOrchestrator instance."""
    orch = await get_orchestrator()
    return orch

@pytest_asyncio.fixture
async def test_user_id():
    """Get or create test user for integration tests."""
    user_id = None
    async with local_session() as db:
        # Search for a specific test user by email
        result = await db.execute(
            select(User).where(User.email == "test_integration@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            try:
                user = User(
                    name="Integration Test User",
                    username="test_mem_int",
                    email="test_integration@example.com",
                    hashed_password="hashed_password",
                    birth_date=datetime(1990, 1, 1).date(),
                    birth_time=datetime(1990, 1, 1, 12, 0).time(),
                    birth_location="London, UK",
                    birth_latitude=51.5074,
                    birth_longitude=-0.1278
                )
                db.add(user)
                await db.commit()
                # Capture ID while session is active and not expired
                user_id = user.id
            except Exception:
                await db.rollback()
                result = await db.execute(
                    select(User).where(User.email == "test_integration@example.com")
                )
                user = result.scalar_one()
                user_id = user.id
        else:
            user_id = user.id
        
        # Ensure profile exists
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id, data={})
            db.add(profile)
            await db.commit()
        
        # Expunge all to avoid DetachedInstanceError later
        db.expunge_all()
    
    yield user_id
    
    # Cleanup profile data for next test
    if user_id:
        async with local_session() as db:
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if profile:
                profile.data = {}
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(profile, 'data')
                await db.commit()

@pytest_asyncio.fixture
async def cleanup_test_cache(memory, test_user_id):
    """Clean up test user's cache before and after tests."""
    async def _cleanup():
        try:
            await memory.invalidate_synthesis(test_user_id)
            await memory.invalidate_module(test_user_id, "astrology")
            await memory.invalidate_module(test_user_id, "human_design")
            await memory.invalidate_module(test_user_id, "numerology")
            
            if memory.redis_client:
                await memory.redis_client.delete(f"memory:hot:history:{test_user_id}")
                await memory.redis_client.delete(f"memory:warm:preferences:{test_user_id}")
        except Exception:
            pass

    await _cleanup()
    yield
    await _cleanup()
