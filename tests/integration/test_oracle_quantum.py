"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               ORACLE QUANTUM ENTROPY - HIGH-FIDELITY TESTS                   ║
║                                                                              ║
║   Tests the complete Oracle + Quantum Entropy pipeline:                      ║
║   1. QuantumEntropy client (bias-free mapping, fallback, API contract)       ║
║   2. OracleService integration (quantum-seeded draws, DB persistence)        ║
║   3. API endpoint (response shape, entropy_source metadata)                  ║
║                                                                              ║
║   Testing Standards:                                                         ║
║   - Real DB/Redis per high-fidelity-testing skill                            ║
║   - Deterministic seeding where possible                                     ║
║   - UTC-aware datetimes                                                      ║
║   - Singleton cleanup                                                        ║
║   - Session isolation (pass db to modules)                                   ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure src is on path
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.app.core.db.database import Base, local_session
from src.app.models.user import User
from src.app.models.user_profile import UserProfile
from src.app.modules.intelligence.oracle.models import OracleReading
from src.app.modules.intelligence.oracle.quantum import QuantumEntropy
from src.app.modules.intelligence.oracle.service import OracleService


# ============================================================================
# SECTION 1: QuantumEntropy Unit Tests (Pure Logic, No Network)
# ============================================================================


class TestQuantumEntropyBiasFreeMapping:
    """
    Validate that the rejection sampling algorithm produces
    zero modulo bias for all Oracle-relevant range sizes.
    """

    def test_rejection_sample_range_13_no_bias(self):
        """
        Cards use range_size=13 (ranks 1-13).
        65536 % 13 = 3, so values >= 65533 should be rejected.
        max_usable = 65536 - 3 = 65533.
        """
        qe = QuantumEntropy()
        max_usable = 65536 - (65536 % 13)  # 65533

        # Values 0 through 65532 should map cleanly
        assert qe._rejection_sample_from_uint16(0, 13) == 0
        assert qe._rejection_sample_from_uint16(12, 13) == 12
        assert qe._rejection_sample_from_uint16(13, 13) == 0  # wraps
        assert qe._rejection_sample_from_uint16(65532, 13) == 65532 % 13

        # Values 65533, 65534, 65535 are in the rejection zone
        for v in [65533, 65534, 65535]:
            with pytest.raises(ValueError, match="rejection zone"):
                qe._rejection_sample_from_uint16(v, 13)

    def test_rejection_sample_range_4_no_bias(self):
        """
        Suits use range_size=4. 65536 % 4 = 0, so NO rejection needed.
        All uint16 values should be usable.
        """
        qe = QuantumEntropy()

        # 65536 is perfectly divisible by 4 - no rejection zone
        assert qe._rejection_sample_from_uint16(0, 4) == 0
        assert qe._rejection_sample_from_uint16(3, 4) == 3
        assert qe._rejection_sample_from_uint16(65535, 4) == 3

    def test_rejection_sample_range_64_no_bias(self):
        """
        Hexagrams use range_size=64. 65536 % 64 = 0, no rejection.
        """
        qe = QuantumEntropy()

        assert qe._rejection_sample_from_uint16(0, 64) == 0
        assert qe._rejection_sample_from_uint16(63, 64) == 63
        assert qe._rejection_sample_from_uint16(65535, 64) == 63

    def test_rejection_sample_range_6_no_bias(self):
        """
        Lines use range_size=6. 65536 % 6 = 4, so values >= 65532 rejected.
        """
        qe = QuantumEntropy()
        max_usable = 65536 - (65536 % 6)  # 65532

        assert qe._rejection_sample_from_uint16(0, 6) == 0
        assert qe._rejection_sample_from_uint16(5, 6) == 5
        assert qe._rejection_sample_from_uint16(65531, 6) == 65531 % 6

        # Values 65532-65535 are in the rejection zone
        for v in [65532, 65533, 65534, 65535]:
            with pytest.raises(ValueError, match="rejection zone"):
                qe._rejection_sample_from_uint16(v, 6)

    def test_rejection_sample_range_1(self):
        """range_size=1 should always return 0."""
        qe = QuantumEntropy()
        assert qe._rejection_sample_from_uint16(0, 1) == 0
        assert qe._rejection_sample_from_uint16(65535, 1) == 0

    def test_rejection_sample_range_invalid(self):
        """range_size <= 0 should raise ValueError."""
        qe = QuantumEntropy()
        with pytest.raises(ValueError, match="range_size must be positive"):
            qe._rejection_sample_from_uint16(100, 0)
        with pytest.raises(ValueError, match="range_size must be positive"):
            qe._rejection_sample_from_uint16(100, -1)

    def test_statistical_uniformity(self):
        """
        Verify that rejection sampling produces uniform distribution
        over a large number of samples (chi-squared test).
        """
        qe = QuantumEntropy()
        range_size = 13  # Card ranks
        counts = [0] * range_size
        n_samples = 100_000

        for _ in range(n_samples):
            raw = secrets.randbelow(65536)
            try:
                val = qe._rejection_sample_from_uint16(raw, range_size)
                counts[val] += 1
            except ValueError:
                pass  # rejection zone, skip

        expected = sum(counts) / range_size

        # Chi-squared test: sum((observed - expected)^2 / expected)
        chi_sq = sum((c - expected) ** 2 / expected for c in counts)

        # For 12 degrees of freedom at p=0.001, critical value is ~32.91
        # We use a generous threshold to avoid flaky tests
        assert chi_sq < 40.0, (
            f"Chi-squared statistic {chi_sq:.2f} exceeds threshold. "
            f"Distribution may be biased. Counts: {counts}"
        )

    def test_min_equals_max_returns_same_value(self):
        """Edge case: min_val == max_val should return that value."""
        qe = QuantumEntropy()
        # This uses LOCAL_CHAOS path since no network needed
        import asyncio
        val, source = asyncio.get_event_loop().run_until_complete(
            qe.get_true_random(42, 42)
        )
        assert val == 42
        assert source == "LOCAL_CHAOS"

    def test_invalid_range_raises(self):
        """min_val > max_val should raise ValueError."""
        qe = QuantumEntropy()
        import asyncio
        with pytest.raises(ValueError, match="min_val"):
            asyncio.get_event_loop().run_until_complete(
                qe.get_true_random(10, 5)
            )


class TestQuantumEntropyLocalFallback:
    """Test that local CSPRNG fallback works correctly."""

    def test_local_rejection_sample_range(self):
        """Local fallback should produce values in correct range."""
        qe = QuantumEntropy()

        for _ in range(1000):
            val = qe._rejection_sample_local(13)
            assert 0 <= val < 13

        for _ in range(1000):
            val = qe._rejection_sample_local(64)
            assert 0 <= val < 64

        for _ in range(1000):
            val = qe._rejection_sample_local(6)
            assert 0 <= val < 6

    def test_local_rejection_sample_range_1(self):
        """range_size=1 should always return 0."""
        qe = QuantumEntropy()
        assert qe._rejection_sample_local(1) == 0

    def test_local_rejection_sample_invalid(self):
        """Invalid range_size should raise."""
        qe = QuantumEntropy()
        with pytest.raises(ValueError):
            qe._rejection_sample_local(0)


# ============================================================================
# SECTION 2: QuantumEntropy Async Tests (Mock Network)
# ============================================================================


class TestQuantumEntropyWithMockedAPI:
    """Test quantum API integration with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_quantum_success_returns_quantum_source(self):
        """Successful ANU API call should return QUANTUM source."""
        qe = QuantumEntropy()

        mock_response = httpx.Response(
            status_code=200,
            json={"success": True, "data": [42000]},
            request=httpx.Request("GET", "https://qrng.anu.edu.au/API/jsonI.php"),
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            value, source = await qe.get_true_random(1, 13)

        assert source == "QUANTUM"
        assert 1 <= value <= 13

    @pytest.mark.asyncio
    async def test_quantum_timeout_falls_back_to_local(self):
        """Timeout should gracefully fall back to LOCAL_CHAOS."""
        qe = QuantumEntropy(timeout_ms=1)  # 1ms timeout

        with patch.object(
            httpx.AsyncClient,
            "get",
            side_effect=httpx.TimeoutException("Connection timed out"),
        ):
            value, source = await qe.get_true_random(1, 64)

        assert source == "LOCAL_CHAOS"
        assert 1 <= value <= 64

    @pytest.mark.asyncio
    async def test_quantum_api_error_falls_back(self):
        """HTTP errors from ANU should fall back to LOCAL_CHAOS."""
        qe = QuantumEntropy()

        mock_response = httpx.Response(status_code=503, text="Service Unavailable")
        mock_response.request = httpx.Request("GET", "https://qrng.anu.edu.au")

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            value, source = await qe.get_true_random(1, 52)

        assert source == "LOCAL_CHAOS"
        assert 1 <= value <= 52

    @pytest.mark.asyncio
    async def test_quantum_malformed_response_falls_back(self):
        """Malformed JSON from ANU should fall back to LOCAL_CHAOS."""
        qe = QuantumEntropy()

        mock_response = httpx.Response(
            status_code=200,
            json={"success": False, "data": []},
            request=httpx.Request("GET", "https://qrng.anu.edu.au/API/jsonI.php"),
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            value, source = await qe.get_true_random(1, 6)

        assert source == "LOCAL_CHAOS"
        assert 1 <= value <= 6

    @pytest.mark.asyncio
    async def test_quantum_network_error_falls_back(self):
        """Network-level errors should fall back to LOCAL_CHAOS."""
        qe = QuantumEntropy()

        with patch.object(
            httpx.AsyncClient,
            "get",
            side_effect=httpx.ConnectError("DNS resolution failed"),
        ):
            value, source = await qe.get_true_random(1, 13)

        assert source == "LOCAL_CHAOS"
        assert 1 <= value <= 13

    @pytest.mark.asyncio
    async def test_quantum_rejection_zone_falls_back(self):
        """
        If ANU returns a value in the rejection zone, it should
        fall back to LOCAL_CHAOS rather than retry the network.
        """
        qe = QuantumEntropy()

        # For range_size=13, max_usable = 65533, so raw=65535 is rejected
        mock_response = httpx.Response(
            status_code=200,
            json={"success": True, "data": [65535]},
            request=httpx.Request("GET", "https://qrng.anu.edu.au/API/jsonI.php"),
        )

        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            value, source = await qe.get_true_random(1, 13)

        assert source == "LOCAL_CHAOS"
        assert 1 <= value <= 13

    @pytest.mark.asyncio
    async def test_card_draw_both_quantum(self):
        """get_card_draw should return QUANTUM only if both calls succeed."""
        qe = QuantumEntropy()

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First call (rank): return 5000 (maps to rank in range)
            # Second call (suit): return 2000 (maps to suit index)
            values = [5000, 2000]
            return httpx.Response(
                status_code=200,
                json={"success": True, "data": [values[call_count - 1]]},
                request=httpx.Request("GET", "https://qrng.anu.edu.au/API/jsonI.php"),
            )

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            rank, suit, source = await qe.get_card_draw()

        assert source == "QUANTUM"
        assert 1 <= rank <= 13
        assert suit in ["Hearts", "Clubs", "Diamonds", "Spades"]

    @pytest.mark.asyncio
    async def test_card_draw_partial_quantum_is_local(self):
        """If one of two draws fails, overall source is LOCAL_CHAOS."""
        qe = QuantumEntropy()

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call succeeds
                return httpx.Response(
                    status_code=200,
                    json={"success": True, "data": [5000]},
                    request=httpx.Request("GET", "https://qrng.anu.edu.au/API/jsonI.php"),
                )
            else:
                # Second call fails
                raise httpx.TimeoutException("timeout")

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            rank, suit, source = await qe.get_card_draw()

        assert source == "LOCAL_CHAOS"
        assert 1 <= rank <= 13
        assert suit in ["Hearts", "Clubs", "Diamonds", "Spades"]

    @pytest.mark.asyncio
    async def test_hexagram_draw_both_quantum(self):
        """get_hexagram_draw should return QUANTUM only if both calls succeed."""
        qe = QuantumEntropy()

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            values = [30000, 3000]
            return httpx.Response(
                status_code=200,
                json={"success": True, "data": [values[call_count - 1]]},
                request=httpx.Request("GET", "https://qrng.anu.edu.au/API/jsonI.php"),
            )

        with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
            hexagram, line, source = await qe.get_hexagram_draw()

        assert source == "QUANTUM"
        assert 1 <= hexagram <= 64
        assert 1 <= line <= 6


# ============================================================================
# SECTION 3: QuantumEntropy Live API Test (Optional, Skippable)
# ============================================================================


class TestQuantumEntropyLiveAPI:
    """
    LIVE tests against the real ANU QRNG API.
    Skipped in CI or if the API is unreachable.
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "--run-live" not in sys.argv,
        reason="Live ANU API tests disabled by default. Use --run-live to enable.",
    )
    async def test_live_anu_api_returns_quantum(self):
        """Hit the real ANU QRNG and verify response shape."""
        qe = QuantumEntropy(timeout_ms=5000)  # generous timeout for live test

        value, source = await qe.get_true_random(1, 64)

        # If the lab is online, we should get QUANTUM
        # If offline, LOCAL_CHAOS (which is still valid)
        assert source in ("QUANTUM", "LOCAL_CHAOS")
        assert 1 <= value <= 64

        if source == "QUANTUM":
            print(f"  Live ANU QRNG returned: {value} (QUANTUM)")
        else:
            print(f"  ANU QRNG unavailable, got: {value} (LOCAL_CHAOS)")


# ============================================================================
# SECTION 4: OracleService Integration Tests (Real DB)
# ============================================================================


class TestOracleServiceQuantumIntegration:
    """
    High-fidelity integration tests for OracleService with Quantum entropy.

    Uses real PostgreSQL database. LLM calls are patched to avoid cost
    and ensure determinism, but everything else is real.
    """

    @pytest_asyncio.fixture
    async def oracle_test_user(self):
        """Create a test user for Oracle tests."""
        async with local_session() as db:
            result = await db.execute(
                select(User).where(User.username == "oracle_test_user")
            )
            user = result.scalar_one_or_none()

            if not user:
                from src.app.core.security import get_password_hash

                user = User(
                    name="Oracle Test",
                    username="oracle_test_user",
                    email="oracle_test@gutters.app",
                    hashed_password=get_password_hash("test_password"),
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)

            # Ensure profile exists
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            profile = result.scalar_one_or_none()

            if not profile:
                profile = UserProfile(
                    user_id=user.id,
                    data={
                        "preferences": {
                            "llm_model": "anthropic/claude-3-haiku-20240307"
                        }
                    },
                )
                db.add(profile)
                await db.commit()

            user_id = user.id

        yield user_id

        # Cleanup: remove test readings
        async with local_session() as db:
            await db.execute(
                OracleReading.__table__.delete().where(
                    OracleReading.user_id == user_id
                )
            )
            await db.commit()

    @pytest.mark.asyncio
    async def test_oracle_draw_records_quantum_entropy_source(
        self, oracle_test_user
    ):
        """
        When quantum API succeeds, the reading should have
        entropy_source='QUANTUM' persisted in the database.
        """
        user_id = oracle_test_user
        service = OracleService()

        # Mock the quantum API to return valid values
        _req = httpx.Request("GET", "https://qrng.anu.edu.au/API/jsonI.php")
        mock_responses = iter([
            httpx.Response(200, json={"success": True, "data": [5000]}, request=_req),
            httpx.Response(200, json={"success": True, "data": [2000]}, request=_req),
            httpx.Response(200, json={"success": True, "data": [30000]}, request=_req),
            httpx.Response(200, json={"success": True, "data": [3000]}, request=_req),
        ])

        async def mock_get(*args, **kwargs):
            return next(mock_responses)

        # Mock LLM to avoid real API calls
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AsyncMock(content="Test synthesis text from the Oracle.")
        )

        with (
            patch.object(httpx.AsyncClient, "get", side_effect=mock_get),
            patch.object(service, "_get_user_llm", return_value=mock_llm),
        ):
            async with local_session() as db:
                reading = await service.perform_daily_draw(user_id, db)

                # Verify reading was created with QUANTUM source
                assert reading.id is not None
                assert reading.entropy_source == "QUANTUM"
                assert 1 <= reading.card_rank <= 13
                assert reading.card_suit in [
                    "Hearts", "Clubs", "Diamonds", "Spades"
                ]
                assert 1 <= reading.hexagram_number <= 64
                assert 1 <= reading.hexagram_line <= 6

                # Verify persistence: re-fetch from DB
                result = await db.execute(
                    select(OracleReading).where(OracleReading.id == reading.id)
                )
                persisted = result.scalar_one()
                assert persisted.entropy_source == "QUANTUM"
                assert persisted.card_rank == reading.card_rank
                assert persisted.card_suit == reading.card_suit

    @pytest.mark.asyncio
    async def test_oracle_draw_records_local_chaos_on_quantum_failure(
        self, oracle_test_user
    ):
        """
        When quantum API fails, reading should have
        entropy_source='LOCAL_CHAOS' persisted in the database.
        """
        user_id = oracle_test_user
        service = OracleService()

        # Mock LLM to avoid real API calls
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AsyncMock(content="Fallback synthesis from chaos.")
        )

        with (
            patch.object(
                httpx.AsyncClient,
                "get",
                side_effect=httpx.TimeoutException("ANU offline"),
            ),
            patch.object(service, "_get_user_llm", return_value=mock_llm),
        ):
            async with local_session() as db:
                reading = await service.perform_daily_draw(user_id, db)

                assert reading.id is not None
                assert reading.entropy_source == "LOCAL_CHAOS"
                assert 1 <= reading.card_rank <= 13
                assert 1 <= reading.hexagram_number <= 64

                # Verify persistence
                result = await db.execute(
                    select(OracleReading).where(OracleReading.id == reading.id)
                )
                persisted = result.scalar_one()
                assert persisted.entropy_source == "LOCAL_CHAOS"

    @pytest.mark.asyncio
    async def test_oracle_draw_with_llm_fallback_still_works(
        self, oracle_test_user
    ):
        """
        Even when BOTH quantum and LLM fail, the draw should
        complete with fallback synthesis and LOCAL_CHAOS entropy.
        """
        user_id = oracle_test_user
        service = OracleService()

        # Mock LLM to fail
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            side_effect=Exception("LLM provider unavailable")
        )

        with (
            patch.object(
                httpx.AsyncClient,
                "get",
                side_effect=httpx.ConnectError("No network"),
            ),
            patch.object(service, "_get_user_llm", return_value=mock_llm),
        ):
            async with local_session() as db:
                reading = await service.perform_daily_draw(user_id, db)

                assert reading.id is not None
                assert reading.entropy_source == "LOCAL_CHAOS"
                # Should use fallback synthesis (contains card name)
                assert "of" in reading.synthesis_text.lower() or "gate" in reading.synthesis_text.lower()
                # Should use fallback question
                assert len(reading.diagnostic_question) > 10

    @pytest.mark.asyncio
    async def test_oracle_draw_card_values_in_valid_range(
        self, oracle_test_user
    ):
        """
        Run multiple draws and verify ALL outputs stay within valid ranges.
        This catches off-by-one errors in the quantum mapping.
        """
        user_id = oracle_test_user
        service = OracleService()

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AsyncMock(content="Range test synthesis.")
        )

        n_draws = 20
        for i in range(n_draws):
            with (
                patch.object(
                    httpx.AsyncClient,
                    "get",
                    side_effect=httpx.TimeoutException("skip quantum for speed"),
                ),
                patch.object(service, "_get_user_llm", return_value=mock_llm),
            ):
                async with local_session() as db:
                    reading = await service.perform_daily_draw(user_id, db)

                    assert 1 <= reading.card_rank <= 13, (
                        f"Draw {i}: card_rank {reading.card_rank} out of range"
                    )
                    assert reading.card_suit in [
                        "Hearts", "Clubs", "Diamonds", "Spades"
                    ], f"Draw {i}: invalid suit {reading.card_suit}"
                    assert 1 <= reading.hexagram_number <= 64, (
                        f"Draw {i}: hexagram {reading.hexagram_number} out of range"
                    )
                    assert 1 <= reading.hexagram_line <= 6, (
                        f"Draw {i}: line {reading.hexagram_line} out of range"
                    )

    @pytest.mark.asyncio
    async def test_oracle_draw_timestamps_are_utc_aware(
        self, oracle_test_user
    ):
        """Verify created_at is timezone-aware UTC."""
        user_id = oracle_test_user
        service = OracleService()

        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AsyncMock(content="UTC test.")
        )

        before = datetime.now(UTC)

        with (
            patch.object(
                httpx.AsyncClient,
                "get",
                side_effect=httpx.TimeoutException("skip"),
            ),
            patch.object(service, "_get_user_llm", return_value=mock_llm),
        ):
            async with local_session() as db:
                reading = await service.perform_daily_draw(user_id, db)

        after = datetime.now(UTC)

        # created_at must be timezone-aware
        assert reading.created_at.tzinfo is not None, (
            "created_at must be timezone-aware"
        )
        assert before <= reading.created_at <= after


# ============================================================================
# SECTION 5: API Endpoint Contract Tests
# ============================================================================


class TestOracleAPIEndpointContract:
    """
    Verify the Oracle API endpoint returns the correct response shape
    including the new entropy_source field.
    """

    @pytest.mark.asyncio
    async def test_draw_response_includes_entropy_source(self):
        """
        The /intelligence/oracle/draw endpoint should return
        entropy_source in the response body.
        """
        from fastapi.testclient import TestClient
        from src.app.main import app
        from src.app.core.db.database import async_get_db
        from src.app.api.dependencies import get_current_user

        # Mock auth
        mock_user = {
            "id": 1,
            "username": "test",
            "email": "test@test.com",
            "name": "Test",
            "is_superuser": False,
        }

        # Mock DB session — endpoint queries UserProfile before calling service
        mock_profile = MagicMock()
        mock_profile.birth_date = None  # No birth date needed for contract test

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async def mock_get_db():
            yield mock_db

        # We test the response schema, not the actual draw
        # So we mock the service
        mock_reading = AsyncMock()
        mock_reading.id = 1
        mock_reading.card_rank = 7
        mock_reading.card_suit = "Spades"
        mock_reading.hexagram_number = 42
        mock_reading.hexagram_line = 3
        mock_reading.synthesis_text = "Test synthesis"
        mock_reading.diagnostic_question = "Test question?"
        mock_reading.entropy_source = "QUANTUM"
        mock_reading.accepted = False
        mock_reading.reflected = False
        mock_reading.created_at = datetime.now(UTC)

        with patch(
            "src.app.modules.intelligence.oracle.OracleService"
        ) as MockService:
            mock_instance = AsyncMock()
            mock_instance.perform_daily_draw = AsyncMock(
                return_value=mock_reading
            )
            MockService.return_value = mock_instance

            app.dependency_overrides[get_current_user] = lambda: mock_user
            app.dependency_overrides[async_get_db] = mock_get_db

            try:
                with TestClient(app) as client:
                    response = client.post("/api/v1/intelligence/oracle/draw")
            finally:
                app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        reading_data = data["reading"]

        # Verify response shape
        assert "entropy_source" in reading_data
        assert reading_data["entropy_source"] == "QUANTUM"
        assert reading_data["card"]["rank"] == 7
        assert reading_data["card"]["suit"] == "Spades"
        assert reading_data["hexagram"]["number"] == 42
        assert reading_data["hexagram"]["line"] == 3
        assert reading_data["synthesis"] == "Test synthesis"
        assert reading_data["diagnostic_question"] == "Test question?"
        assert "created_at" in reading_data


# ============================================================================
# SECTION 6: Boundary and Edge Case Tests
# ============================================================================


class TestQuantumEntropyEdgeCases:
    """Edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_uint16_boundary_values(self):
        """Test all uint16 boundary values for range_size=52 (full deck)."""
        qe = QuantumEntropy()
        range_size = 52
        max_usable = 65536 - (65536 % range_size)  # 65520

        # Value at max_usable boundary
        assert qe._rejection_sample_from_uint16(max_usable - 1, range_size) == (max_usable - 1) % range_size

        # Values in rejection zone
        for v in range(max_usable, 65536):
            with pytest.raises(ValueError, match="rejection zone"):
                qe._rejection_sample_from_uint16(v, range_size)

    @pytest.mark.asyncio
    async def test_all_suits_reachable(self):
        """Verify all 4 suits are reachable from quantum values."""
        qe = QuantumEntropy()

        reached_suits = set()
        for raw in range(0, 4):
            idx = qe._rejection_sample_from_uint16(raw, 4)
            suits = ["Hearts", "Clubs", "Diamonds", "Spades"]
            reached_suits.add(suits[idx])

        assert reached_suits == {"Hearts", "Clubs", "Diamonds", "Spades"}

    @pytest.mark.asyncio
    async def test_all_ranks_reachable(self):
        """Verify all 13 ranks are reachable from quantum values."""
        qe = QuantumEntropy()

        reached_ranks = set()
        for raw in range(0, 13):
            val = qe._rejection_sample_from_uint16(raw, 13)
            reached_ranks.add(val + 1)

        assert reached_ranks == set(range(1, 14))

    @pytest.mark.asyncio
    async def test_all_hexagrams_reachable(self):
        """Verify all 64 hexagrams are reachable from quantum values."""
        qe = QuantumEntropy()

        reached = set()
        for raw in range(0, 64):
            val = qe._rejection_sample_from_uint16(raw, 64)
            reached.add(val + 1)

        assert reached == set(range(1, 65))

    @pytest.mark.asyncio
    async def test_all_lines_reachable(self):
        """Verify all 6 lines are reachable from quantum values."""
        qe = QuantumEntropy()

        reached = set()
        for raw in range(0, 6):
            val = qe._rejection_sample_from_uint16(raw, 6)
            reached.add(val + 1)

        assert reached == set(range(1, 7))

    @pytest.mark.asyncio
    async def test_concurrent_draws_dont_interfere(self):
        """Multiple concurrent draws should not share state."""
        import asyncio

        qe = QuantumEntropy()

        async def draw():
            with patch.object(
                httpx.AsyncClient,
                "get",
                side_effect=httpx.TimeoutException("skip"),
            ):
                return await qe.get_true_random(1, 64)

        results = await asyncio.gather(*[draw() for _ in range(50)])

        # All results should be valid
        for val, source in results:
            assert 1 <= val <= 64
            assert source == "LOCAL_CHAOS"

        # Should not all be the same (probabilistic, but 50 identical
        # values from range 1-64 is astronomically unlikely)
        values = {v for v, _ in results}
        assert len(values) > 1, "All 50 concurrent draws returned the same value"
