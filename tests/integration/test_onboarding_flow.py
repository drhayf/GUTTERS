"""
Integration tests for onboarding flow.

Tests the complete user journey:
1. Check onboarding status (should be incomplete)
2. Submit birth data
3. Calculate profile (all modules)
4. Retrieve synthesis
5. Check onboarding status (should be complete)
"""

from datetime import date, time, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.security import create_access_token
from src.app.models.user import User
from src.app.models.user_profile import UserProfile


@pytest_asyncio.fixture
async def auth_headers(test_user: User):
    """Generate auth headers for test user."""
    access_token = await create_access_token(data={"sub": test_user.username}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.mark.asyncio
async def test_onboarding_flow_complete(
    client: AsyncClient, db: AsyncSession, test_user: User, auth_headers: dict, memory
):
    """Test complete onboarding flow from start to finish."""

    # Step 0: Ensure fresh start (reset birth data)
    test_user.birth_date = None
    test_user.birth_time = None
    test_user.birth_location = None
    test_user.birth_latitude = None
    test_user.birth_longitude = None
    test_user.birth_timezone = None
    await db.commit()
    await db.refresh(test_user)

    # Step 1: Check initial onboarding status
    response = client.get("/api/v1/profile/onboarding-status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["onboarding_completed"] is False
    assert data["has_birth_data"] is False
    assert data["has_calculated_profile"] is False
    assert data["has_synthesis"] is False

    # Step 2: Get available modules
    response = client.get("/api/v1/profile/modules", headers=auth_headers)
    assert response.status_code == 200
    modules_data = response.json()
    assert "modules" in modules_data
    assert modules_data["total_modules"] >= 3  # At minimum: astrology, HD, numerology

    # Step 3: Submit birth data
    birth_data = {
        "birth_date": "1990-01-15",
        "birth_time": "14:30:00",
        "birth_location": "San Francisco, CA, USA",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timezone": "America/Los_Angeles",
        "time_unknown": False,
    }

    response = client.post("/api/v1/profile/birth-data", json=birth_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify user was updated
    await db.refresh(test_user)
    assert test_user.birth_date == date(1990, 1, 15)
    assert test_user.birth_time == time(14, 30, 0)
    assert test_user.birth_location == "San Francisco, CA, USA"

    # Step 4: Calculate profile
    response = client.post("/api/v1/profile/calculate", headers=auth_headers)
    assert response.status_code == 200
    calc_data = response.json()
    assert calc_data["success"] is True
    assert len(calc_data["modules_calculated"]) >= 3
    assert "synthesis_preview" in calc_data

    # Verify profile data
    from sqlalchemy import select

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user.id))
    profile = result.scalar_one()

    # Check all modules calculated
    for module_name in calc_data["modules_calculated"]:
        assert module_name in profile.data
        assert "error" not in profile.data[module_name]

    # Check synthesis exists
    assert "onboarding_synthesis" in profile.data
    synthesis = profile.data["onboarding_synthesis"]
    # synthesis is a dict when dumped via model_dump(mode='json')
    assert "synthesis" in synthesis or "synthesis_text" in synthesis
    assert "modules_included" in synthesis
    assert len(synthesis["modules_included"]) == len(calc_data["modules_calculated"])

    # Step 5: Retrieve synthesis
    response = client.get("/api/v1/profile/synthesis", headers=auth_headers)
    assert response.status_code == 200
    synth_data = response.json()
    assert "synthesis" in synth_data
    assert len(synth_data["synthesis"]) > 20  # Should be substantial text
    assert synth_data["modules_count"] >= 3

    # Step 6: Check final onboarding status
    response = client.get("/api/v1/profile/onboarding-status", headers=auth_headers)
    assert response.status_code == 200
    final_status = response.json()
    assert final_status["onboarding_completed"] is True
    assert final_status["has_birth_data"] is True
    assert final_status["has_calculated_profile"] is True
    assert final_status["has_synthesis"] is True
    assert len(final_status["modules_calculated"]) >= 3


@pytest.mark.asyncio
async def test_onboarding_unknown_birth_time(
    client: AsyncClient, db: AsyncSession, test_user: User, auth_headers: dict, memory
):
    """Test onboarding with unknown birth time (some modules may be skipped)."""

    # Submit birth data without time
    birth_data = {
        "birth_date": "1990-01-15",
        "birth_time": None,
        "birth_location": "San Francisco, CA, USA",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timezone": "America/Los_Angeles",
        "time_unknown": True,
    }

    response = client.post("/api/v1/profile/birth-data", json=birth_data, headers=auth_headers)
    assert response.status_code == 200

    # Get modules (should include ALL modules now, even without time)
    response = client.get("/api/v1/profile/modules", headers=auth_headers)
    assert response.status_code == 200
    modules = response.json()

    # Verify all modules are present
    module_names = [m["name"] for m in modules["modules"]]
    assert "numerology" in module_names
    assert "astrology" in module_names
    assert "human_design" in module_names

    # Calculate profile
    response = client.post("/api/v1/profile/calculate", headers=auth_headers)
    assert response.status_code == 200
    calc_data = response.json()

    # Should succeed with all modules calculated
    assert calc_data["success"] is True
    assert len(calc_data["modules_calculated"]) >= 3

    # Check that modules returned probabilistic data
    from sqlalchemy import select

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user.id))
    profile = result.scalar_one()

    # Check Astrology (should be probabilistic)
    astro_data = profile.data.get("astrology", {})
    assert astro_data.get("accuracy") == "probabilistic"
    assert "rising_probabilities" in astro_data

    # Check Human Design (should be probabilistic)
    hd_data = profile.data.get("human_design", {})
    assert hd_data.get("accuracy") == "probabilistic"
    assert "type_probabilities" in hd_data


@pytest.mark.asyncio
async def test_module_registry_discovery(client: AsyncClient, auth_headers: dict, memory):
    """Test that module registry correctly discovers all registered modules."""

    response = client.get("/api/v1/profile/modules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "modules" in data
    assert "total_modules" in data
    assert "total_weight" in data

    # Verify each module has required fields
    for module in data["modules"]:
        assert "name" in module
        assert "display_name" in module
        assert "description" in module
        assert "weight" in module
        assert "progress_percentage" in module
        assert "requires_birth_time" in module

    # Verify progress percentages sum to ~100
    total_progress = sum(m["progress_percentage"] for m in data["modules"])
    assert 99 <= total_progress <= 101  # Allow for floating point rounding
