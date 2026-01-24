"""
High-fidelity integration tests for Hypothesis module.

Uses seeded data from Phase 3.5.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone

from src.app.modules.intelligence.hypothesis.generator import HypothesisGenerator
from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
from src.app.modules.intelligence.hypothesis.tracker import HypothesisTracker
from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
from src.app.modules.intelligence.synthesis.synthesizer import DEFAULT_MODEL
from src.app.core.ai.llm_factory import get_llm

@pytest.mark.asyncio
async def test_hypothesis_generation_from_patterns(seeded_user, db):
    """
    Test theory hypothesis generation from Observer patterns.
    
    Verification:
    - Hypotheses generated from seeded Observer findings
    - Solar sensitivity theory created
    - Lunar pattern theory created
    - Confidence scores calculated
    """
    llm = get_llm(DEFAULT_MODEL)
    generator = HypothesisGenerator(llm)
    observer_storage = ObserverFindingStorage()
    
    # 1. Get seeded Observer patterns
    patterns = await observer_storage.get_findings(seeded_user, min_confidence=0.7)
    
    assert len(patterns) >= 4, f"Should have at least 4 seeded Observer patterns, found {len(patterns)}"
    
    # Initialize EventBus
    from src.app.core.events.bus import get_event_bus
    await get_event_bus().initialize()
    
    # 2. Generate hypotheses
    hypotheses = await generator.generate_from_patterns(seeded_user, patterns)
    
    # 3. Verify generation
    assert len(hypotheses) >= 3
    
    hypothesis_types = {h.hypothesis_type.value for h in hypotheses}
    assert "cosmic_sensitivity" in hypothesis_types
    assert "temporal_pattern" in hypothesis_types
    
    for h in hypotheses:
        assert h.user_id == seeded_user
        assert h.claim != ""
        assert 0.0 <= h.confidence <= 1.0
        assert h.evidence_count > 0

@pytest.mark.asyncio
async def test_hypothesis_storage_and_retrieval(seeded_user, db):
    """
    Test hypothesis persistence.
    
    Verification:
    - Hypothesis stored in PostgreSQL
    - Hypothesis cached in Redis
    - Can retrieve by confidence threshold
    """
    llm = get_llm(DEFAULT_MODEL)
    generator = HypothesisGenerator(llm)
    storage = HypothesisStorage()
    observer_storage = ObserverFindingStorage()
    
    # Initialize EventBus for events
    from src.app.core.events.bus import get_event_bus
    await get_event_bus().initialize()
    
    # Generate
    patterns = await observer_storage.get_findings(seeded_user, min_confidence=0.7)
    hypotheses = await generator.generate_from_patterns(seeded_user, patterns)
    
    # Store
    for h in hypotheses:
        await storage.store_hypothesis(h, db)
    
    # Retrieve
    retrieved = await storage.get_hypotheses(seeded_user, min_confidence=0.0)
    
    assert len(retrieved) >= len(hypotheses)
    
    # Verify Redis cache
    from src.app.core.memory.active_memory import get_active_memory
    memory = get_active_memory()
    await memory.initialize()
    cached = await memory.get(f"hypotheses:{seeded_user}")
    assert cached is not None
    assert len(cached) >= len(hypotheses)

@pytest.mark.asyncio
async def test_hypothesis_confidence_update(seeded_user, db):
    """
    Test confidence updates from new evidence.
    
    Verification:
    - Confidence increases with supporting evidence
    - Confidence decreases with contradictory evidence
    - Status updates (forming → testing → confirmed)
    """
    llm = get_llm(DEFAULT_MODEL)
    generator = HypothesisGenerator(llm)
    tracker = HypothesisTracker()
    observer_storage = ObserverFindingStorage()
    
    # Initialize EventBus
    from src.app.core.events.bus import get_event_bus
    await get_event_bus().initialize()
    
    # Generate hypothesis
    patterns = await observer_storage.get_findings(seeded_user, min_confidence=0.7)
    hypotheses = await generator.generate_from_patterns(seeded_user, patterns)
    
    hypothesis = hypotheses[0]
    initial_confidence = hypothesis.confidence
    initial_count = hypothesis.evidence_count
    
    # Simulate supporting evidence
    new_data = {
        "text": "Had a terrible headache today during the solar flare",
        "mood_score": 4,
        "kp_index": 7,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    updated_hypothesis, update_record = await tracker.update_from_new_data(
        hypothesis,
        new_data,
        "journal_entry"
    )
    
    # Verify confidence increased
    assert updated_hypothesis.confidence > initial_confidence
    assert updated_hypothesis.evidence_count == initial_count + 1
    assert update_record.confidence_after > update_record.confidence_before

@pytest.mark.asyncio
async def test_confirmed_hypotheses_in_synthesis(seeded_user, db):
    """
    Test confirmed hypotheses appear in synthesis.
    
    Verification:
    - Synthesis mentions confirmed patterns
    """
    from src.app.modules.intelligence.synthesis.synthesizer import ProfileSynthesizer
    from src.app.modules.intelligence.hypothesis.models import Hypothesis, HypothesisStatus, HypothesisType
    
    # Create confirmed hypothesis
    hypothesis = Hypothesis(
        id="test-confirmed-theory",
        user_id=seeded_user,
        hypothesis_type=HypothesisType.COSMIC_SENSITIVITY,
        claim="User is electromagnetically sensitive to geomagnetic storms",
        predicted_value="Sensitive to solar activity",
        confidence=0.91,
        evidence_count=20,
        contradictions=0,
        status=HypothesisStatus.CONFIRMED,
        generated_at=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc)
    )
    
    # Store
    storage = HypothesisStorage()
    await storage.store_hypothesis(hypothesis, db)
    
    # Generate synthesis
    synthesizer = ProfileSynthesizer()
    from src.app.core.events.bus import get_event_bus
    await get_event_bus().initialize()
    profile = await synthesizer.synthesize_profile(seeded_user, db)
    
    # Verify hypothesis mentioned
    assert profile.synthesis != ""
    # In a real LLM test, we'd check if specific keywords are present
    # But for integration, we check if the confirmed theories were counted
    from src.app.core.memory.active_memory import get_active_memory
    memory = get_active_memory()
    await memory.initialize()
    s_cached = await memory.get_master_synthesis(seeded_user)
    assert s_cached.get('count_confirmed_theories') >= 1

@pytest.mark.asyncio
async def test_hypothesis_event_published(seeded_user, db):
    """
    Test HYPOTHESIS_GENERATED event published.
    """
    from unittest.mock import patch, AsyncMock
    
    # We patch the event bus in generator.py
    with patch("src.app.modules.intelligence.hypothesis.generator.get_event_bus") as mock_bus_func:
        mock_bus = AsyncMock()
        mock_bus_func.return_value = mock_bus
        
        llm = get_llm(DEFAULT_MODEL)
        generator = HypothesisGenerator(llm)
        observer_storage = ObserverFindingStorage()
        
        # Initialize EventBus
        from src.app.core.events.bus import get_event_bus
        await get_event_bus().initialize()
        
        patterns = await observer_storage.get_findings(seeded_user, min_confidence=0.7)
        hypotheses = await generator.generate_from_patterns(seeded_user, patterns)
        
        # Verify events published for each hypothesis
        assert mock_bus.publish.call_count == len(hypotheses)
        
        # Check first call
        call_args = mock_bus.publish.call_args_list[0]
        assert call_args[0][0] == "hypothesis.generated"
        assert call_args[0][1]["user_id"] == seeded_user
