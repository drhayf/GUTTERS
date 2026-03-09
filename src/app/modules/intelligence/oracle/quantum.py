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
from typing import List, Literal, Tuple

import httpx
import structlog

logger = structlog.get_logger(__name__)

# ANU Quantum Random Numbers Server
ANU_QRNG_URL = "https://qrng.anu.edu.au/API/jsonI.php"
ANU_TIMEOUT_MS = 3000  # 3 second cap — single batched call instead of 4 rapid-fire

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

    Performance:
        Fetches all needed random values in a SINGLE batched API call
        to avoid rate-limiting and connection overhead.
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

    async def _fetch_quantum_uint16(self, count: int = 1) -> int | List[int]:
        """
        Fetch uint16 value(s) (0–65535) from the ANU Quantum API.

        Args:
            count: Number of uint16 values to fetch in a single call.

        Returns:
            Single raw integer if count=1, list of ints if count>1.

        Raises:
            httpx.TimeoutException: If API doesn't respond within timeout.
            httpx.HTTPStatusError: If API returns non-200 status.
            ValueError: If API response is malformed.
        """
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(
                ANU_QRNG_URL,
                params={"length": count, "type": "uint16"},
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                raise ValueError(f"ANU QRNG returned failure: {data}")

            numbers = data.get("data", [])
            if len(numbers) < count:
                raise ValueError(f"ANU QRNG returned {len(numbers)} values, expected {count}")

            for val in numbers:
                v = int(val)
                if not (0 <= v <= 65535):
                    raise ValueError(f"ANU QRNG value out of uint16 range: {v}")

            if count == 1:
                return int(numbers[0])
            return [int(n) for n in numbers]

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

    async def get_full_oracle_draw(
        self,
    ) -> Tuple[int, str, int, int, EntropySource]:
        """
        Draw a complete Oracle reading (card + hexagram) in a SINGLE
        batched API call.

        This is the preferred method — it fetches all 4 random values
        from ANU QRNG in one HTTP request, avoiding rate-limit failures
        that occur with 4 sequential calls.

        Returns:
            Tuple of (card_rank, suit_name, hexagram_number, line, entropy_source).
            entropy_source is QUANTUM only if ALL values came from the batch.
        """
        suits = ["Hearts", "Clubs", "Diamonds", "Spades"]

        try:
            # Single batched call — 4 uint16 values in one request
            raw_values = await self._fetch_quantum_uint16(count=4)
            if not isinstance(raw_values, list) or len(raw_values) < 4:
                raise ValueError(f"Expected 4 values, got {raw_values}")

            # Apply rejection sampling to each value
            rank_val = self._rejection_sample_from_uint16(raw_values[0], 13)
            suit_val = self._rejection_sample_from_uint16(raw_values[1], 4)
            hex_val = self._rejection_sample_from_uint16(raw_values[2], 64)
            line_val = self._rejection_sample_from_uint16(raw_values[3], 6)

            card_rank = 1 + rank_val      # [1, 13]
            suit_name = suits[suit_val]   # index [0, 3]
            hexagram = 1 + hex_val        # [1, 64]
            line = 1 + line_val           # [1, 6]

            logger.info(
                "quantum.oracle.batch_success",
                raw=raw_values,
                card=f"{card_rank} of {suit_name}",
                hexagram=hexagram,
                line=line,
            )

            return card_rank, suit_name, hexagram, line, "QUANTUM"

        except Exception as e:
            logger.warning(
                "quantum.oracle.batch_fallback",
                error=str(e),
                reason="Falling back to individual draws with OS CSPRNG",
            )

        # Fallback: use the individual methods (which use LOCAL_CHAOS)
        card_rank, suit_name, card_source = await self.get_card_draw()
        hexagram, line, hex_source = await self.get_hexagram_draw()

        combined_source: EntropySource = (
            "QUANTUM" if card_source == "QUANTUM" and hex_source == "QUANTUM"
            else "LOCAL_CHAOS"
        )

        return card_rank, suit_name, hexagram, line, combined_source
