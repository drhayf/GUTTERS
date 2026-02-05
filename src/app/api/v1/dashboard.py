import logging
from datetime import UTC, datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_current_user
from src.app.core.db.database import async_get_db
from src.app.core.memory.active_memory import get_active_memory
from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
from src.app.modules.intelligence.observer.observer import Observer
from src.app.modules.tracking.solar.tracker import SolarTracker
from src.app.modules.tracking.lunar.tracker import LunarTracker
from src.app.modules.tracking.transits.tracker import TransitTracker
from src.app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# ============================================================================
# RESPONSE MODELS
# ============================================================================


class DashboardSummaryResponse(BaseModel):
    """High-level dashboard summary."""

    user_name: str
    synthesis_preview: str
    modules_active: list[str]
    last_updated: str
    confidence_score: float


class IntelligenceFeedItem(BaseModel):
    """Unified feed item for Observer patterns and Hypotheses."""

    id: str
    type: str  # "pattern" or "hypothesis"
    title: str
    description: str
    confidence: float
    timestamp: str
    metadata: dict[str, Any]


class CosmicWidgetResponse(BaseModel):
    """Current cosmic weather."""

    moon_phase: str
    moon_sign: str
    sun_sign: str
    active_transits_count: int
    geomagnetic_index: float
    # Extended fields for enhanced frontend
    bz: float | None = None
    solar_wind_speed: float | None = None
    shield_integrity: str | None = None
    is_voc: bool = False
    retrograde_count: int = 0


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Get high-level dashboard summary (Synthesis + Core Stats).
    Uses Active Memory for speed.
    """
    user_id = current_user["id"]
    memory = get_active_memory()
    await memory.initialize()

    # 1. Try Hot Memory (Synthesis)
    synthesis_data = await memory.get_master_synthesis(user_id)

    # 2. Fallback to DB if cold
    if not synthesis_data or synthesis_data.get("validity") == "stale":
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if profile and profile.data:
            synth = profile.data.get("onboarding_synthesis") or profile.data.get("synthesis")
            if synth:
                synthesis_data = {
                    "synthesis": synth.get("synthesis_text") or synth.get("synthesis", ""),
                    "generated_at": synth.get("timestamp"),
                    "modules_included": synth.get("modules_included", []),
                    "confidence": synth.get("confidence", 0.0),
                }

    if not synthesis_data:
        # Default empty state
        return DashboardSummaryResponse(
            user_name=current_user["name"] or current_user["username"],
            synthesis_preview="Profile not yet synthesized. Please complete onboarding.",
            modules_active=[],
            last_updated=datetime.now(timezone.utc).isoformat(),
            confidence_score=0.0,
        )

    return DashboardSummaryResponse(
        user_name=current_user["name"] or current_user["username"],
        synthesis_preview=synthesis_data.get("synthesis", "")[:200] + "...",
        modules_active=synthesis_data.get("modules_included", []),
        last_updated=synthesis_data.get("generated_at") or datetime.now(UTC).isoformat(),
        confidence_score=synthesis_data.get("confidence", 0.0),
    )


@router.get("/intelligence", response_model=list[IntelligenceFeedItem])
async def get_intelligence_feed(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Unified intelligence feed:
    1. Active Hypotheses (from Hypothesis module)
    2. Detected Patterns (from Observer module)
    """
    user_id = current_user["id"]
    feed = []

    # --- 1. Get Hypotheses ---
    storage = HypothesisStorage()
    hypotheses = await storage.get_hypotheses(user_id, min_confidence=0.4)

    for h in hypotheses:
        feed.append(
            IntelligenceFeedItem(
                id=h.id,
                type="hypothesis",
                title=f"Theory: {h.claim}",
                description=h.predicted_value,
                confidence=h.confidence,
                timestamp=h.last_updated.isoformat(),
                metadata={"status": h.status.value, "evidence_count": h.evidence_count},
            )
        )

    # --- 2. Get Observer Patterns ---
    # Observer computes on the fly for now (caching later)
    observer = Observer()

    # Run detectors (concurrently ideally, but sequential for safety first)
    try:
        solar_patterns = await observer.detect_solar_correlations(user_id, db)
        lunar_patterns = await observer.detect_lunar_correlations(user_id, db)
        time_patterns = await observer.detect_time_based_patterns(user_id, db)

        all_patterns = solar_patterns + lunar_patterns + time_patterns

        for idx, p in enumerate(all_patterns):
            feed.append(
                IntelligenceFeedItem(
                    id=f"pattern-{idx}-{user_id}",
                    type="pattern",
                    title=f"Pattern: {p['pattern_type'].replace('_', ' ').title()}",
                    description=p["finding"],
                    confidence=p["confidence"],
                    timestamp=p["detected_at"],
                    metadata=p,
                )
            )

    except Exception as e:
        logger.error(f"Error generating observer patterns: {e}")
        # Don't fail the whole request
        pass

    # Sort by timestamp desc
    feed.sort(key=lambda x: x.timestamp, reverse=True)

    return feed


@router.get("/cosmic", response_model=CosmicWidgetResponse)
async def get_cosmic_widget(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Get current cosmic conditions.
    """
    user_id = current_user["id"]

    # 1. Solar Data
    solar_tracker = SolarTracker()
    solar_data = await solar_tracker.fetch_current_data()

    # 2. Lunar Data
    lunar_tracker = LunarTracker()
    lunar_data = await lunar_tracker.fetch_current_data()

    # 3. Transit Data
    transit_tracker = TransitTracker()
    current_transit_data = await transit_tracker.fetch_current_data()

    # Compare to natal for active count
    comparison = await transit_tracker.compare_to_natal(user_id, current_transit_data)

    positions = current_transit_data.data.get("positions", {})
    moon_pos = positions.get("Moon", {})
    sun_pos = positions.get("Sun", {})

    # Count retrograde planets
    retrograde_count = sum(1 for p in positions.values() if p.get("is_retrograde", False))

    return CosmicWidgetResponse(
        moon_phase=lunar_data.data.get("phase_name", "Unknown"),
        moon_sign=moon_pos.get("sign") or lunar_data.data.get("sign", "Unknown"),
        sun_sign=sun_pos.get("sign", "Unknown"),
        active_transits_count=comparison.get("total_transits", 0),
        geomagnetic_index=solar_data.data.get("kp_index", 0.0),
        # Extended fields
        bz=solar_data.data.get("bz"),
        solar_wind_speed=solar_data.data.get("solar_wind_speed"),
        shield_integrity=solar_data.data.get("shield_integrity"),
        is_voc=lunar_data.data.get("is_voc", False),
        retrograde_count=retrograde_count,
    )
