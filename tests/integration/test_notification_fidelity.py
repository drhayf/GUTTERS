import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import select
from src.app.models.user_profile import UserProfile
from src.app.modules.infrastructure.push.router import notification_router


@pytest.mark.asyncio
async def test_notification_preferences_persistence(client, test_user, db):
    """
    Verify that PATCH /profile/preferences correctly updates the database (High Fidelity).
    """
    # 1. Login
    # (Client fixture in conftest usually handles auth if using test_user, or we use overrides.
    # Checking conftest: client fixture uses dependency_overrides? No, it yields client.
    # We need to authenticate. Since we have 'test_user' fixture, let's override get_current_user logic or just use force interaction if possible.)
    # Actually, simpler: TestClient + dependency override for auth is standard pattern in this codebase.

    from src.app.api.dependencies import get_current_user

    app = client.app
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username}

    # 2. Update Preference (Disable Solar)
    payload = {"notifications": {"solar": False}}
    response = client.patch("/api/v1/profile/preferences", json=payload)
    assert response.status_code == 200

    # 3. Verify in DB (Real Persistence check)
    # Must use a new session or refresh to ensure we see the committed data
    # The 'db' fixture is an async session. We can use it to query.
    # Note: Client runs in sync thread usually, async tests need care.
    # With TestClient, the app runs in the same thread.

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user.id))
    profile = result.scalar_one()

    prefs = profile.data.get("preferences", {}).get("notifications", {})
    assert prefs["solar"] is False
    assert prefs.get("lunar", True) is True  # Default check


@pytest.mark.asyncio
async def test_notification_router_generic_filtering(db, test_user):
    """
    Verify NotificationRouter respects generic 'intelligence' preferences.
    """
    # 1. Setup User Profile with Intelligence DISABLED
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=test_user.id, data={})
        db.add(profile)

    profile.data = {"preferences": {"notifications": {"intelligence": False}}}
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(profile, "data")
    await db.commit()

    # 2. Patch Service
    with patch(
        "src.app.modules.infrastructure.push.service.NotificationService.send_to_user", new_callable=AsyncMock
    ) as mock_send:
        # 3. Trigger Hypothesis Update (via generic packet handler)
        from src.app.protocol.packet import Packet

        packet = Packet(
            event_type="hypothesis.updated", payload={"trait": "Manifestor", "confidence": 0.8}, source="test"
        )

        await notification_router.handle_event_packet(packet)

        # 4. Assert NOT called
        calls_for_user = [c for c in mock_send.call_args_list if c.kwargs.get("user_id") == test_user.id]
        assert len(calls_for_user) == 0, "Should not send intelligence alert when disabled"


@pytest.mark.asyncio
async def test_notification_router_generic_delivery(db, test_user):
    """
    Verify NotificationRouter delivers 'intelligence' events when enabled.
    """
    # 1. Setup User Profile with Intelligence ENABLED
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=test_user.id, data={})
        db.add(profile)

    profile.data = {"preferences": {"notifications": {"intelligence": True}}}
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(profile, "data")
    await db.commit()

    # 2. Patch Service
    with patch(
        "src.app.modules.infrastructure.push.service.NotificationService.send_to_user", new_callable=AsyncMock
    ) as mock_send:
        # 3. Trigger Hypothesis Update
        from src.app.protocol.packet import Packet

        packet = Packet(
            event_type="hypothesis.updated", payload={"trait": "Manifestor", "confidence": 0.8}, source="test"
        )

        await notification_router.handle_event_packet(packet)

        # 4. Assert CALLED and FORMATTED
        calls_for_user = [c for c in mock_send.call_args_list if c.kwargs.get("user_id") == test_user.id]
        assert len(calls_for_user) == 1
        assert "Pattern Detected" in calls_for_user[0].kwargs["title"]
        assert "Manif" in calls_for_user[0].kwargs["body"]  # Template check


@pytest.mark.asyncio
async def test_notification_router_filtering(db, test_user):
    """
    Verify NotificationRouter respects preferences (Logic Check).
    """
    # 1. Setup User Profile with Cosmic DISABLED
    # We use direct DB manipulation to set up state (High Fidelity state setup)
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=test_user.id, data={})
        db.add(profile)

    # Updated to 'cosmic' key per new map
    profile.data = {"preferences": {"notifications": {"cosmic": False}}}
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(profile, "data")
    await db.commit()

    # 2. Patch the external service call (The only allowed mock)
    # We want to verify if 'send_to_user' calls the underlying push logic.
    # Let's patch 'src.app.modules.infrastructure.push.service.NotificationService.send_to_user'
    with patch(
        "src.app.modules.infrastructure.push.service.NotificationService.send_to_user", new_callable=AsyncMock
    ) as mock_send:
        # 3. Trigger Cosmic Update (High Intensity)
        from src.app.protocol.packet import Packet

        payload = {"kp_index": 8, "kp_status": "Storm", "moon_phase": "Waning Gibbous"}
        packet = Packet(event_type="cosmic_update", payload=payload, source="test")

        await notification_router.handle_event_packet(packet)

        # 4. Assert NOT called for this user
        calls_for_user = [c for c in mock_send.call_args_list if c.kwargs.get("user_id") == test_user.id]
        assert len(calls_for_user) == 0, "Should not send cosmic alert when disabled"


@pytest.mark.asyncio
async def test_notification_router_delivery(db, test_user):
    """
    Verify NotificationRouter sends when enabled (Happy Path).
    """
    # 1. Setup User Profile with Cosmic ENABLED
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == test_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=test_user.id, data={})
        db.add(profile)

    profile.data = {"preferences": {"notifications": {"cosmic": True}}}
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(profile, "data")
    await db.commit()

    # 2. Patch Service
    with patch(
        "src.app.modules.infrastructure.push.service.NotificationService.send_to_user", new_callable=AsyncMock
    ) as mock_send:
        # 3. Trigger Update
        from src.app.protocol.packet import Packet

        payload = {"kp_index": 8, "kp_status": "Storm", "moon_phase": "Waning Gibbous"}
        packet = Packet(event_type="cosmic_update", payload=payload, source="test")

        await notification_router.handle_event_packet(packet)

        # 4. Assert CALLED
        calls_for_user = [c for c in mock_send.call_args_list if c.kwargs.get("user_id") == test_user.id]
        assert len(calls_for_user) == 1, "Should send cosmic alert when enabled"
        assert "Cosmic Alert" in calls_for_user[0].kwargs["title"]
