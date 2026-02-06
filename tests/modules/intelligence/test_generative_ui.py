"""
Tests for Generative UI system.

Verifies component generation and response handling using high-fidelity standards.
"""

import uuid

import pytest
from sqlalchemy import select

from src.app.core.llm.config import get_premium_llm
from src.app.core.memory import get_active_memory
from src.app.models.user_profile import UserProfile
from src.app.modules.intelligence.generative_ui.generator import ComponentGenerator
from src.app.modules.intelligence.generative_ui.models import (
    ComponentResponse,
    ComponentSpec,
    ComponentType,
    MoodSliderSpec,
)
from src.app.modules.intelligence.query.engine import QueryEngine


@pytest.mark.asyncio
async def test_models_serialization():
    """Test that component models serialize to JSON correctly."""
    spec = ComponentSpec(
        component_type=ComponentType.MOOD_SLIDER,
        mood_slider=MoodSliderSpec(question="Mood?", slider_config={"id": "mood", "min_value": 1, "max_value": 10}),
    )

    # Dump to JSON-compatible dict
    data = spec.model_dump(mode="json")
    assert data["component_type"] == "mood_slider"
    assert "mood_slider" in data
    assert data["mood_slider"]["question"] == "Mood?"

    # Verify deserialization
    reconstructed = ComponentSpec(**data)
    assert reconstructed.component_id == spec.component_id
    assert reconstructed.mood_slider.question == spec.mood_slider.question


@pytest.mark.asyncio
async def test_generator_multi_slider():
    """Test generating a multi-slider component."""
    generator = ComponentGenerator()

    spec = await generator.generate_multi_slider(message="I felt anxious and tired today", context={})

    assert spec.component_type == ComponentType.MULTI_SLIDER
    assert spec.multi_slider is not None
    assert len(spec.multi_slider.sliders) == 3

    slider_ids = [s.id for s in spec.multi_slider.sliders]
    assert "mood" in slider_ids
    assert "energy" in slider_ids
    assert "anxiety" in slider_ids

    # Verify strict serialization for frontend
    json_data = spec.model_dump(mode="json")
    assert json_data["component_type"] == "multi_slider"


@pytest.mark.asyncio
async def test_query_engine_integration(seeded_user, db):
    """
    Test QueryEngine integration with component generation.
    Uses real DB and Redis.
    """
    memory = get_active_memory()
    await memory.initialize()

    # Setup engine with Generative UI enabled
    engine = QueryEngine(llm=get_premium_llm(), memory=memory, enable_generative_ui=True)

    # We can't easily force the LLM to generate a component in a live test without
    # specific prompting or mocking the generator's decision method.
    # Here we'll patch just the decision method to force generation,
    # to verify the pipeline handles it correctly.

    async def mock_decision(*args):
        return True, ComponentType.MULTI_SLIDER

    engine.component_generator.should_generate_component = mock_decision

    response = await engine.answer_query(user_id=seeded_user, question="I'm feeling very overwhelmed right now.", db=db)

    assert response.component is not None
    assert response.component.component_type == ComponentType.MULTI_SLIDER
    assert response.component.multi_slider is not None

    # Verify it appears in trace
    assert response.trace is not None
    # We can check trace steps... but verifying component present is enough for integration


@pytest.mark.asyncio
async def test_api_component_submission(seeded_user, db, memory):
    """
    Test submitting a component response via API logic directly.
    (We verify the logic inside the endpoint handler pattern).
    """
    # Simulate API handler logic
    from src.app.api.v1.chat import submit_component_response

    # Create a component response
    comp_id = str(uuid.uuid4())
    payload = ComponentResponse(
        component_id=comp_id,
        component_type=ComponentType.MULTI_SLIDER,
        slider_values={"mood": 5, "energy": 3, "anxiety": 8},
        interaction_time_ms=1500,
    )

    # Call handler (simulated)
    # We need a user object matching the seeded_user ID
    from src.app.models.user import User

    user = User(id=seeded_user, email="test@example.com")

    result = await submit_component_response(response=payload, current_user=user, db=db)

    assert result["success"] is True
    assert result["component_id"] == comp_id

    # Verify storage in DB
    updated_profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == seeded_user))

    # Check component_responses
    matches = [r for r in updated_profile.data.get("component_responses", []) if r["component_id"] == comp_id]
    assert len(matches) == 1
    assert matches[0]["slider_values"]["anxiety"] == 8

    # Check journal entry creation
    journal_entries = updated_profile.data.get("journal_entries", [])
    assert len(journal_entries) > 0
    latest_entry = journal_entries[-1]
    assert latest_entry["source"] == "multi_slider_component"
    assert "Mood: 5/10" in latest_entry["content"]
    assert "Anxiety: 8/10" in latest_entry["content"]
