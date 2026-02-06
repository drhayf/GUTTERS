"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      QUANTUM ENTROPY CLIENT                                  ║
║                                                                              ║
║   Sources true randomness from quantum vacuum fluctuations via the           ║
║   ANU Quantum Random Numbers Server (QRNG).                                 ║
║                                                                              ║
║   Fallback: Cryptographic OS entropy (secrets.SystemRandom) if the           ║
║   quantum source is unavailable.                                             ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import math
import secrets
from typing import Literal, Tuple

import httpx
import structlog

logger = structlog.get_logger(__name__)

# ANU Quantum Random Numbers Server
ANU_QRNG_URL = "https://qrng.anu.edu.au/API/jsonI.php"
ANU_TIMEOUT_MS = 1000  # 1 second hard cap — UI must never hang

EntropySource = Literal["QUANTUM", "LOCAL_CHAOS"]


class QuantumEntropy:
    """
    Quantum-seeded entropy source with cryptographic fallback.

    Architecture:
        1. PRIMARY: ANU QRNG — photonic quantum vacuum fluctuations
        2. FALLBACK: secrets.SystemRandom — OS-level CSPRNG (/dev/urandom)

    Both sources are cryptographically suitable. The quantum source adds
    "true" (non-deterministic) randomness from physical phenomena rather
    than algorithmic PRNG.
    """

    def __init__(self, timeout_ms: int = ANU_TIMEOUT_MS):
        """
        Args:
            timeout_ms: Maximum wait time for quantum API in milliseconds.
        """
        self._timeout_seconds = timeout_ms / 1000.0
        self._system_random = secrets.SystemRandom()

    async def get_true_random(
        self, min_val: int, max_val: int
    ) -> Tuple[int, EntropySource]:
        """
        Generate a random integer in [min_val, max_val] inclusive.

        Tries quantum source first; falls back to OS CSPRNG on failure.
        Uses rejection sampling to eliminate modulo bias.

        Args:
            min_val: Minimum value (inclusive).
            max_val: Maximum value (inclusive).

        Returns:
            Tuple of (random_value, entropy_source).

        Raises:
            ValueError: If min_val > max_val.
        """
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")

        if min_val == max_val:
            return min_val, "LOCAL_CHAOS"

        range_size = max_val - min_val + 1

        # Try quantum source first
        try:
            raw_quantum = await self._fetch_quantum_uint16()
            value = self._rejection_sample_from_uint16(raw_quantum, range_size)
            result = min_val + value
            logger.info(
                "quantum.entropy.success",
                raw=raw_quantum,
                mapped=result,
                range=f"[{min_val}, {max_val}]",
            )
            return result, "QUANTUM"

        except Exception as e:
            logger.warning(
                "quantum.entropy.fallback",
                error=str(e),
                reason="Falling back to OS CSPRNG",
            )

        # Fallback: cryptographic OS entropy with rejection sampling
        value = self._rejection_sample_local(range_size)
        result = min_val + value
        logger.info(
            "quantum.entropy.local_chaos",
            mapped=result,
            range=f"[{min_val}, {max_val}]",
        )
        return result, "LOCAL_CHAOS"

    async def _fetch_quantum_uint16(self) -> int:
        """
        Fetch a single uint16 (0–65535) from the ANU Quantum API.

        Returns:
            Raw quantum random integer in range [0, 65535].

        Raises:
            httpx.TimeoutException: If API doesn't respond within timeout.
            httpx.HTTPStatusError: If API returns non-200 status.
            ValueError: If API response is malformed.
        """
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(
                ANU_QRNG_URL,
                params={"length": 1, "type": "uint16"},
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                raise ValueError(f"ANU QRNG returned failure: {data}")

            numbers = data.get("data", [])
            if not numbers:
                raise ValueError(f"ANU QRNG returned no data: {data}")

            raw_value = int(numbers[0])
            if not (0 <= raw_value <= 65535):
                raise ValueError(f"ANU QRNG value out of uint16 range: {raw_value}")

            return raw_value

    @staticmethod
    def _rejection_sample_from_uint16(raw: int, range_size: int) -> int:
        """
        Map a uint16 to [0, range_size) with ZERO modulo bias.

        Uses rejection sampling: we compute the largest multiple of
        range_size that fits in 65536, and reject values above it.

        For our use cases (range_size <= 64), the rejection probability
        is at most 64/65536 ≈ 0.1%, so this essentially never triggers.
        But if it does, we fall back to local CSPRNG rather than retry
        the network call.

        Args:
            raw: Raw uint16 value [0, 65535].
            range_size: Number of possible outcomes.

        Returns:
            Unbiased value in [0, range_size).

        Raises:
            ValueError: If raw value falls in the rejection zone
                        (caller should fall back to local entropy).
        """
        if range_size <= 0:
            raise ValueError(f"range_size must be positive, got {range_size}")

        if range_size == 1:
            return 0

        # Number of complete "buckets" that fit in 65536
        max_usable = 65536 - (65536 % range_size)

        if raw >= max_usable:
            raise ValueError(
                f"Quantum value {raw} in rejection zone "
                f"(>= {max_usable} for range {range_size}). "
                f"Falling back to local entropy."
            )

        return raw % range_size

    def _rejection_sample_local(self, range_size: int) -> int:
        """
        Generate unbiased random value in [0, range_size) using OS CSPRNG.

        Uses the same rejection sampling technique but can retry locally
        since there's no network cost.

        Args:
            range_size: Number of possible outcomes.

        Returns:
            Unbiased value in [0, range_size).
        """
        if range_size <= 0:
            raise ValueError(f"range_size must be positive, got {range_size}")

        if range_size == 1:
            return 0

        # Use secrets.randbelow which already handles rejection sampling
        # internally via the same principle. It's the gold standard.
        return secrets.randbelow(range_size)

    async def get_card_draw(self) -> Tuple[int, str, EntropySource]:
        """
        Draw a random card (rank 1-13, suit).

        Returns:
            Tuple of (rank, suit_name, entropy_source).
            entropy_source reflects the LEAST secure source used.
        """
        suits = ["Hearts", "Clubs", "Diamonds", "Spades"]

        rank, rank_source = await self.get_true_random(1, 13)
        suit_idx, suit_source = await self.get_true_random(0, 3)

        # The overall source is only QUANTUM if BOTH draws were quantum
        combined_source: EntropySource = (
            "QUANTUM" if rank_source == "QUANTUM" and suit_source == "QUANTUM"
            else "LOCAL_CHAOS"
        )

        return rank, suits[suit_idx], combined_source

    async def get_hexagram_draw(self) -> Tuple[int, int, EntropySource]:
        """
        Draw a random hexagram (1-64) and line (1-6).

        Returns:
            Tuple of (hexagram_number, line, entropy_source).
            entropy_source reflects the LEAST secure source used.
        """
        hexagram, hex_source = await self.get_true_random(1, 64)
        line, line_source = await self.get_true_random(1, 6)

        combined_source: EntropySource = (
            "QUANTUM" if hex_source == "QUANTUM" and line_source == "QUANTUM"
            else "LOCAL_CHAOS"
        )

        return hexagram, line, combined_source
