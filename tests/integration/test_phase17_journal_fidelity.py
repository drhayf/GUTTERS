from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_current_user
from src.app.main import app
from src.app.models.insight import PromptStatus, ReflectionPrompt
from src.app.models.user import User


@pytest.mark.asyncio
async def test_phase17_journal_fidelity(
    db: AsyncSession,
    test_user: User,
):
    """
    High-Fidelity Test for Phase 17: Journal UI & Insight Integration.
    """

    # ---------------------------------------------------------
    # 0. SETUP: Auth Override & Async Client
    # ---------------------------------------------------------
    # Mock auth dependency to return our test_user
    app.dependency_overrides[get_current_user] = lambda: {"id": test_user.id, "username": test_user.username}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # ---------------------------------------------------------
        # 1. SETUP: Create a Pending Reflection Prompt
        # ---------------------------------------------------------
        prompt = ReflectionPrompt(
            user_id=test_user.id,
            prompt_text="The Full Moon is peaking. How is your sleep?",
            topic="lunar_peak",
            status=PromptStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        db.add(prompt)
        await db.commit()
        await db.refresh(prompt)

        print(f"\n[SETUP] Created Prompt ID: {prompt.id}")

        # ---------------------------------------------------------
        # 2. VERIFY: Fetch Pending Prompts (ActiveReflections UI)
        # ---------------------------------------------------------
        response = await client.get("/api/v1/insights/prompts")
        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        fetched_prompt = next(p for p in data if p["id"] == prompt.id)
        assert fetched_prompt["prompt_text"] == prompt.prompt_text
        assert fetched_prompt["topic"] == "lunar_peak"

        print("[PASS] GET /api/v1/insights/prompts returned correct data.")

        # ---------------------------------------------------------
        # 3. VERIFY: Submit Journal Entry with Context (ContextualComposer UI)
        # ---------------------------------------------------------
        context_snapshot = {
            "moon_phase": "Full Moon",
            "geomagnetic_index": 7,
            "client_time": datetime.now(UTC).isoformat(),
        }

        payload = {
            "content": "I felt restless all night, probably the moon.",
            "mood_score": 5,
            "tags": ["sleep", "moon"],
            "prompt_id": prompt.id,
            "context_snapshot": context_snapshot,
        }

        response = await client.post("/api/v1/insights/journal", json=payload)
        assert response.status_code == 200
        entry_data = response.json()

        assert entry_data["content"] == payload["content"]
        assert entry_data["context_snapshot"]["moon_phase"] == "Full Moon"

        print("[PASS] POST /api/v1/insights/journal succeeded with Context Snapshot.")

        # ---------------------------------------------------------
        # 4. VERIFY: Prompt Status Update (Backend Logic)
        # ---------------------------------------------------------
        await db.refresh(prompt)
        assert prompt.status == PromptStatus.ANSWERED

        print(f"[PASS] Prompt {prompt.id} status updated to ANSWERED.")

        # ---------------------------------------------------------
        # 5. VERIFY: List Entries (LivingArchive UI)
        # ---------------------------------------------------------
        response = await client.get("/api/v1/insights/journal")
        assert response.status_code == 200
        entries = response.json()

        fetched_entry = next(e for e in entries if e["id"] == entry_data["id"])

        # Check Fidelity elements for UI
        assert fetched_entry["context_snapshot"] is not None
        assert fetched_entry["context_snapshot"]["geomagnetic_index"] == 7
        assert "moon" in fetched_entry["tags"]

        print("[PASS] GET /api/v1/insights/journal returned entry with robust metadata.")

    # Cleanup dependency override
    app.dependency_overrides = {}
