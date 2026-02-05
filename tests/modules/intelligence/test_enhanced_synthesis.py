"""
High-fidelity integration tests for Enhanced Synthesis.
"""
import pytest
from sqlalchemy import select
from datetime import datetime

from src.app.models.user_profile import UserProfile
from src.app.core.memory.active_memory import get_active_memory
from src.app.core.db.database import local_session as async_session_maker
from src.app.core.events.bus import get_event_bus

@pytest.mark.asyncio
async def test_hierarchical_synthesis_with_seeded_data(seeded_user):
    from src.app.modules.intelligence.synthesis.synthesizer import ProfileSynthesizer
    
    await get_event_bus().initialize()
    memory = get_active_memory()
    await memory.initialize()
    
    synthesizer = ProfileSynthesizer()
    async with async_session_maker() as db:
        profile = await synthesizer.synthesize_profile(seeded_user, db)
        assert profile.synthesis is not None
        assert len(profile.modules_included) >= 1
        
        cached = await memory.get_master_synthesis(seeded_user)
        assert cached is not None

@pytest.mark.asyncio
async def test_synthesis_includes_journal_patterns(seeded_user):
    from src.app.modules.intelligence.synthesis.synthesizer import ProfileSynthesizer
    await get_event_bus().initialize()
    
    synthesizer = ProfileSynthesizer()
    async with async_session_maker() as db:
        profile = await synthesizer.synthesize_profile(seeded_user, db)
        synthesis_lower = profile.synthesis.lower()
        
        patterns = ["headache", "moon", "anxious", "sunday", "energy", "creative"]
        assert any(p in synthesis_lower for p in patterns)

@pytest.mark.asyncio
async def test_synthesis_persistence(seeded_user):
    from src.app.modules.intelligence.synthesis.synthesizer import ProfileSynthesizer
    await get_event_bus().initialize()
    
    synthesizer = ProfileSynthesizer()
    async with async_session_maker() as db:
        await synthesizer.synthesize_profile(seeded_user, db)
    
    async with async_session_maker() as db:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == seeded_user))
        profile = result.scalar_one()
        assert "synthesis" in profile.data

@pytest.mark.asyncio
async def test_module_synthesis_parallel_generation(seeded_user):
    from src.app.modules.intelligence.synthesis.module_synthesis import ModuleSynthesizer
    from src.app.core.ai.llm_factory import get_llm
    from src.app.modules.intelligence.synthesis.synthesizer import DEFAULT_MODEL
    
    module_synthesizer = ModuleSynthesizer(get_llm(DEFAULT_MODEL))
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
    storage = ObserverFindingStorage()
    findings = await storage.get_findings(seeded_user)
    
    observer_synth = await module_synthesizer.synthesize_observer_patterns(findings)
    assert len(observer_synth) > 50

@pytest.mark.asyncio
async def test_synthesis_event_published(seeded_user):
    from unittest.mock import patch, AsyncMock
    from src.app.protocol.events import SYNTHESIS_GENERATED
    from src.app.modules.intelligence.synthesis.synthesizer import ProfileSynthesizer
    
    with patch("src.app.core.events.bus.get_event_bus") as mock_bus:
        mock_instance = AsyncMock()
        mock_bus.return_value = mock_instance
        
        synthesizer = ProfileSynthesizer()
        async with async_session_maker() as db:
            await synthesizer.synthesize_profile(seeded_user, db)
        
        assert any(call[0][0] == SYNTHESIS_GENERATED for call in mock_instance.publish.call_args_list)
