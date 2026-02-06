import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends

from src.app.api.dependencies import get_current_user
from src.app.core.db.database import async_get_db

router = APIRouter(prefix="/observer", tags=["observer"])
logger = logging.getLogger(__name__)


@router.get("/findings")
async def get_findings(
    current_user: Annotated[dict, Depends(get_current_user)],
    min_confidence: float = 0.6
):
    """Get Observer findings for current user."""
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage

    storage = ObserverFindingStorage()
    findings = await storage.get_findings(current_user["id"], min_confidence)

    return {
        "findings": findings,
        "total": len(findings)
    }


@router.post("/analyze")
async def trigger_analysis(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Manually trigger Observer analysis.

    This endpoint:
    1. Runs all Observer detection methods (including cyclical patterns)
    2. Stores new findings
    3. Updates existing hypotheses with pattern evidence
    4. Generates new hypotheses from cyclical patterns
    """
    from src.app.core.ai.llm import get_llm
    from src.app.modules.intelligence.hypothesis.generator import HypothesisGenerator
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    from src.app.modules.intelligence.hypothesis.updater import get_hypothesis_updater
    from src.app.modules.intelligence.observer.observer import Observer
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage

    observer = Observer()
    storage = ObserverFindingStorage()
    hypothesis_updater = get_hypothesis_updater()
    hypothesis_storage = HypothesisStorage()

    async for db in async_get_db():
        # Run full analysis (includes cyclical patterns)
        analysis_results = await observer.run_full_analysis(current_user["id"], db)

        solar = analysis_results["solar"]
        lunar = analysis_results["lunar"]
        transits = analysis_results["transits"]
        time_patterns = analysis_results["time_patterns"]
        cyclical = analysis_results["cyclical"]

        all_findings = solar + lunar + transits + time_patterns

        # Store non-cyclical findings (cyclical are stored separately)
        for finding in all_findings:
            await storage.store_finding(current_user["id"], finding, db)

        # Update existing hypotheses with new pattern evidence
        hypotheses_updated = 0
        existing_hypotheses = await hypothesis_storage.get_hypotheses(current_user["id"])

        # Update with standard findings
        for finding in all_findings:
            for hypothesis in existing_hypotheses:
                if _pattern_relates_to_hypothesis(finding, hypothesis):
                    try:
                        await hypothesis_updater.add_pattern_evidence(
                            hypothesis=hypothesis,
                            pattern=finding,
                            db=db,
                            magi_context=None
                        )
                        hypotheses_updated += 1
                        logger.info(
                            f"[Observer] Updated hypothesis {hypothesis.id} "
                            f"with {finding['pattern_type']} pattern evidence"
                        )
                    except Exception as e:
                        logger.warning(
                            f"[Observer] Failed to update hypothesis {hypothesis.id}: {e}"
                        )

        # Generate hypotheses from cyclical patterns
        hypotheses_generated = 0
        if cyclical:
            try:
                llm = await get_llm()
                generator = HypothesisGenerator(llm)
                new_hypotheses = await generator.generate_from_cyclical_patterns(
                    current_user["id"],
                    cyclical
                )

                for hypothesis in new_hypotheses:
                    await hypothesis_storage.store_hypothesis(hypothesis)
                    hypotheses_generated += 1
                    logger.info(
                        f"[Observer] Generated hypothesis {hypothesis.id} "
                        f"from cyclical pattern"
                    )
            except Exception as e:
                logger.warning(f"[Observer] Failed to generate from cyclical patterns: {e}")

        return {
            "status": "complete",
            "findings_detected": len(all_findings) + len(cyclical),
            "hypotheses_updated": hypotheses_updated,
            "hypotheses_generated": hypotheses_generated,
            "solar": len(solar),
            "lunar": len(lunar),
            "transits": len(transits),
            "time_patterns": len(time_patterns),
            "cyclical": len(cyclical)
        }


def _pattern_relates_to_hypothesis(pattern: Dict[str, Any], hypothesis) -> bool:
    """
    Check if a detected pattern relates to an existing hypothesis.

    Uses pattern type and hypothesis type for matching.
    """
    from src.app.modules.intelligence.hypothesis.models import HypothesisStatus, HypothesisType

    # Skip rejected/stale hypotheses
    if hypothesis.status in [HypothesisStatus.REJECTED, HypothesisStatus.STALE]:
        return False

    pattern_type = pattern.get("pattern_type", "")

    # Pattern type to hypothesis type mapping
    pattern_hypothesis_map = {
        "solar_symptom": [HypothesisType.COSMIC_SENSITIVITY],
        "lunar_phase": [HypothesisType.COSMIC_SENSITIVITY],
        "transit_theme": [HypothesisType.TRANSIT_EFFECT, HypothesisType.THEME_CORRELATION],
        "day_of_week": [HypothesisType.TEMPORAL_PATTERN],
        "cyclical": [HypothesisType.CYCLICAL_PATTERN, HypothesisType.TEMPORAL_PATTERN],
    }

    compatible_types = pattern_hypothesis_map.get(pattern_type, [])

    if hypothesis.hypothesis_type not in compatible_types:
        return False

    # Additional semantic matching based on pattern details
    if pattern_type == "solar_symptom":
        # Check if hypothesis claim mentions similar symptoms
        symptom = pattern.get("symptom", "")
        return symptom.lower() in hypothesis.claim.lower()

    elif pattern_type == "lunar_phase":
        # Check if hypothesis relates to same phase
        phase = pattern.get("phase", "")
        return phase.lower() in hypothesis.claim.lower()

    elif pattern_type == "transit_theme":
        # Check theme alignment
        theme = pattern.get("theme", "")
        return theme.lower() in hypothesis.claim.lower()

    elif pattern_type == "day_of_week":
        # Check day match
        day = pattern.get("day", "")
        return day.lower() in hypothesis.claim.lower()

    # Default: compatible type is enough
    return True


@router.get("/questions")
async def get_questions(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Get questions generated from findings."""
    from src.app.modules.intelligence.observer.observer import Observer
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage

    storage = ObserverFindingStorage()
    findings = await storage.get_findings(current_user["id"], min_confidence=0.7)

    observer = Observer()
    questions = observer.generate_questions(findings)

    return {
        "questions": questions,
        "based_on_findings": len(findings)
    }


# ============================================================================
# Cyclical Pattern Endpoints
# ============================================================================

@router.get("/cyclical")
async def get_cyclical_patterns(
    current_user: Annotated[dict, Depends(get_current_user)],
    min_confidence: float = 0.5,
    pattern_type: str | None = None
):
    """
    Get detected cyclical patterns aligned with magi periods.

    Returns patterns grouped by type:
    - period_specific_symptom: Symptoms recurring during specific planet periods
    - inter_period_mood_variance: Mood/energy differences between periods
    - theme_alignment: Journal content matching period themes
    - cross_year_evolution: Trends across multiple yearly cycles

    Args:
        min_confidence: Minimum confidence threshold (default: 0.5)
        pattern_type: Filter by specific pattern type (optional)

    Returns:
        List of cyclical patterns with statistics
    """
    from src.app.modules.intelligence.observer.cyclical import CyclicalPatternStorage, CyclicalPatternType

    storage = CyclicalPatternStorage()
    patterns = await storage.get_patterns(current_user["id"], min_confidence)

    # Filter by pattern type if specified
    if pattern_type:
        try:
            target_type = CyclicalPatternType(pattern_type)
            patterns = [p for p in patterns if p.pattern_type == target_type]
        except ValueError:
            pass  # Invalid type, return all

    # Group by type for easier consumption
    grouped = {}
    for pattern in patterns:
        ptype = pattern.pattern_type.value if hasattr(pattern.pattern_type, 'value') else pattern.pattern_type
        if ptype not in grouped:
            grouped[ptype] = []
        grouped[ptype].append(pattern.model_dump(mode="json"))

    return {
        "patterns": [p.model_dump(mode="json") for p in patterns],
        "grouped": grouped,
        "total": len(patterns),
        "by_type": {k: len(v) for k, v in grouped.items()}
    }


@router.post("/cyclical/analyze")
async def analyze_cyclical_patterns(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Trigger cyclical pattern analysis.

    Runs all cyclical detection methods:
    1. Period-specific symptom detection
    2. Inter-period mood/energy variance
    3. Theme alignment analysis
    4. Cross-year evolution tracking

    Optionally generates hypotheses from detected patterns.

    Returns:
        Analysis results with detected patterns and statistics
    """
    from src.app.core.ai.llm import get_llm
    from src.app.modules.intelligence.hypothesis.generator import HypothesisGenerator
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    from src.app.modules.intelligence.observer.observer import Observer

    observer = Observer()

    async for db in async_get_db():
        # Run cyclical pattern detection
        patterns = await observer.detect_cyclical_patterns(current_user["id"], db)

        # Generate hypotheses from patterns
        hypotheses_generated = 0
        spawned_hypothesis_ids = []

        if patterns:
            try:
                llm = await get_llm()
                generator = HypothesisGenerator(llm)
                hypothesis_storage = HypothesisStorage()

                new_hypotheses = await generator.generate_from_cyclical_patterns(
                    current_user["id"],
                    patterns
                )

                for hypothesis in new_hypotheses:
                    await hypothesis_storage.store_hypothesis(hypothesis)
                    hypotheses_generated += 1
                    spawned_hypothesis_ids.append(hypothesis.id)
                    logger.info(
                        f"[Observer] Generated hypothesis {hypothesis.id} "
                        f"from cyclical pattern"
                    )
            except Exception as e:
                logger.warning(f"[Observer] Failed to generate from cyclical patterns: {e}")

        # Group patterns by type
        by_type = {}
        for p in patterns:
            ptype = p.get("pattern_type", "unknown")
            by_type[ptype] = by_type.get(ptype, 0) + 1

        return {
            "status": "complete",
            "patterns_detected": len(patterns),
            "patterns": patterns,
            "by_type": by_type,
            "hypotheses_generated": hypotheses_generated,
            "spawned_hypothesis_ids": spawned_hypothesis_ids
        }


@router.get("/cyclical/summary")
async def get_cyclical_summary(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Get a summary of cyclical pattern insights for the user.

    Returns key findings about:
    - Most sensitive planetary periods
    - Mood/energy variation across periods
    - Theme alignment strengths
    - Long-term evolution trends
    """
    from src.app.modules.intelligence.observer.cyclical import CyclicalPatternStorage, CyclicalPatternType

    storage = CyclicalPatternStorage()
    patterns = await storage.get_patterns(current_user["id"], min_confidence=0.6)

    if not patterns:
        return {
            "status": "insufficient_data",
            "message": "Not enough data to detect cyclical patterns. Continue journaling for more accurate insights.",
            "summary": None
        }

    # Build summary
    summary = {
        "strongest_patterns": [],
        "sensitive_periods": [],
        "best_period": None,
        "challenging_period": None,
        "evolution_trends": [],
        "theme_alignments": []
    }

    # Find strongest patterns (top 3 by confidence)
    sorted_patterns = sorted(patterns, key=lambda x: x.confidence, reverse=True)
    summary["strongest_patterns"] = [
        {
            "type": p.pattern_type.value if hasattr(p.pattern_type, 'value') else p.pattern_type,
            "finding": p.finding,
            "confidence": p.confidence
        }
        for p in sorted_patterns[:3]
    ]

    # Find sensitive periods (symptom patterns)
    symptom_patterns = [
        p for p in patterns
        if p.pattern_type == CyclicalPatternType.PERIOD_SPECIFIC_SYMPTOM
    ]
    for p in symptom_patterns:
        summary["sensitive_periods"].append({
            "planet": p.planet.value if hasattr(p.planet, 'value') and p.planet else None,
            "symptom": p.symptom,
            "occurrence_rate": p.occurrence_rate,
            "fold_increase": p.fold_increase
        })

    # Find best/challenging periods (mood variance)
    mood_patterns = [
        p for p in patterns
        if p.pattern_type == CyclicalPatternType.INTER_PERIOD_MOOD_VARIANCE
    ]
    if mood_patterns:
        best_pattern = max(mood_patterns, key=lambda x: x.high_value or 0)
        summary["best_period"] = {
            "planet": (
                best_pattern.planet_high.value
                if hasattr(best_pattern.planet_high, 'value') and best_pattern.planet_high
                else None
            ),
            "avg_mood": best_pattern.high_value
        }
        summary["challenging_period"] = {
            "planet": (
                best_pattern.planet_low.value
                if hasattr(best_pattern.planet_low, 'value') and best_pattern.planet_low
                else None
            ),
            "avg_mood": best_pattern.low_value
        }

    # Evolution trends
    evolution_patterns = [
        p for p in patterns
        if p.pattern_type == CyclicalPatternType.CROSS_YEAR_EVOLUTION
    ]
    for p in evolution_patterns:
        summary["evolution_trends"].append({
            "planet": p.planet.value if hasattr(p.planet, 'value') and p.planet else None,
            "trend": p.trend_direction,
            "years_tracked": p.years_tracked,
            "finding": p.finding
        })

    # Theme alignments
    theme_patterns = [
        p for p in patterns
        if p.pattern_type == CyclicalPatternType.THEME_ALIGNMENT
    ]
    for p in theme_patterns:
        summary["theme_alignments"].append({
            "planet": p.planet.value if hasattr(p.planet, 'value') and p.planet else None,
            "theme": p.period_theme,
            "alignment_score": p.alignment_score
        })

    return {
        "status": "complete",
        "total_patterns": len(patterns),
        "summary": summary
    }
