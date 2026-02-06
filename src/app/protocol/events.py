"""
GUTTERS Event Constants

Defines all event type constants used throughout GUTTERS.
Using constants prevents typos and enables IDE autocomplete.

Event Naming Convention:
    {CATEGORY}_{ACTION}

    Categories: USER, MODULE, COSMIC, SYNTHESIS
    Actions: Past tense verbs (CREATED, UPDATED, DETECTED, etc.)
"""

# ============================================================================
# User Events
# ============================================================================
# Triggered when user-related changes occur

USER_CREATED = "user.created"
"""User account created. Payload: {user_id: UUID, email: str}"""

USER_BIRTH_DATA_UPDATED = "user.birth_data_updated"
"""User birth data changed. Payload: {user_id: UUID, birth_datetime: datetime, location: dict}"""

USER_PREFERENCES_CHANGED = "user.preferences_changed"
"""User preferences updated. Payload: {user_id: UUID, preferences: dict}"""


# ============================================================================
# Module Events
# ============================================================================
# Triggered by individual GUTTERS modules

MODULE_INITIALIZED = "module.initialized"
"""Module completed initialization. Payload: {module_name: str, layer: str, version: str}"""

MODULE_PROFILE_CALCULATED = "module.profile_calculated"
"""Module calculated user profile. Payload: {module_name: str, user_id: UUID, profile_data: dict}"""

MODULE_ERROR = "module.error"
"""Module encountered error. Payload: {module_name: str, error: str, traceback: str}"""


# ============================================================================
# Cosmic Events
# ============================================================================
# Triggered by cosmic tracking modules

COSMIC_STORM_DETECTED = "cosmic.storm.detected"
"""Solar storm detected. Payload: {kp_index: float, timestamp: datetime, severity: str}"""

COSMIC_FULL_MOON = "cosmic.full_moon"
"""Full moon occurring. Payload: {timestamp: datetime, sign: str, degree: float}"""

COSMIC_TRANSIT_EXACT = "cosmic.transit.exact"
"""Planetary transit exact. Payload: {planet: str, aspect: str, natal_planet: str, user_id: UUID}"""

# --- Granular Tracking Events ---

COSMIC_SOLAR_ALERT = "cosmic.solar.alert"
"""Solar weather alert (Kp spike, Bz flip, high-speed stream).
Payload: {event_name: str, kp_index: float, bz: float, shield_integrity: str,
user_id: int}"""

COSMIC_AURORA_ALERT = "cosmic.aurora.alert"
"""Aurora visible or possible at user location.
Payload: {aurora_status: str, probability: float, latitude: float, hemisphere: str,
user_id: int}"""

COSMIC_GEOMAGNETIC_IMPACT = "cosmic.geomagnetic.impact"
"""Location-specific geomagnetic impact alert.
Payload: {severity: str, effects: list, geomag_lat: float, user_id: int}"""

COSMIC_LUNAR_VOC_START = "cosmic.lunar.voc_start"
"""Void of Course period begins. Payload: {moon_sign: str, duration_hours: float, next_ingress: str, user_id: int}"""

COSMIC_LUNAR_VOC_END = "cosmic.lunar.voc_end"
"""Void of Course period ends (sign ingress). Payload: {new_sign: str, user_id: int}"""

COSMIC_LUNAR_PHASE = "cosmic.lunar.phase"
"""Significant lunar phase (New/Full Moon).
Payload: {phase_name: str, moon_sign: str, illumination: float, user_id: int}"""

COSMIC_RETROGRADE_START = "cosmic.retrograde.start"
"""Planet enters retrograde. Payload: {planet: str, sign: str, duration_days: int, user_id: int}"""

COSMIC_RETROGRADE_END = "cosmic.retrograde.end"
"""Planet goes direct (retrograde ends). Payload: {planet: str, sign: str, user_id: int}"""

COSMIC_PLANET_STATION = "cosmic.planet.station"
"""Planet stationing (near-zero velocity). Payload: {planet: str, sign: str, station_type: str, user_id: int}"""

COSMIC_INGRESS = "cosmic.ingress"
"""Planet enters new sign. Payload: {planet: str, new_sign: str, old_sign: str, user_id: int}"""


# ============================================================================
# Synthesis Events
# ============================================================================
# Triggered by master synthesis engine

SYNTHESIS_TRIGGERED = "synthesis.triggered"
"""Synthesis process started. Payload: {user_id: UUID, trigger_reason: str}"""

SYNTHESIS_COMPLETED = "synthesis.completed"
"""Synthesis process finished. Payload: {user_id: UUID, synthesis_id: UUID, insights_count: int}"""

SYNTHESIS_UPDATED = "synthesis.updated"
"""Synthesis data updated. Payload: {user_id: UUID, synthesis_id: UUID, updated_fields: list}"""

SYNTHESIS_GENERATED = "synthesis.profile.generated"
"""Hierarchical synthesis generated. Payload: SynthesisGeneratedPayload"""

SYNTHESIS_CACHED = "synthesis.cache.updated"
"""Synthesis cached in active memory. Payload: {user_id: int}"""

MODULE_SYNTHESIS_GENERATED = "synthesis.module.generated"
"""Module-specific synthesis generated. Payload: {user_id: int, module: str}"""


# ============================================================================
# Magi (Cardology) Events
# ============================================================================
# Triggered by the Chronos-Magi Time-Mapping Engine

MAGI_PROFILE_CALCULATED = "magi.profile.calculated"
"""Cardology profile computed for user. Payload: {user_id: int, birth_card: str, planetary_card: str, year: int}"""

MAGI_PERIOD_SHIFT = "magi.period.shift"
"""52-day planetary period changed.
Payload: {user_id: int, old_planet: str, new_planet: str, old_card: str,
new_card: str, period_number: int}"""

MAGI_YEAR_SHIFT = "magi.year.shift"
"""Personal cardology year rolled over.
Payload: {user_id: int, old_age: int, new_age: int, old_planetary_card: str,
new_planetary_card: str}"""

MAGI_STATE_CACHED = "magi.state.cached"
"""Chronos state cached to Redis. Payload: {user_id: int, current_planet: str, current_card: str, ttl: int}"""


# ============================================================================
# I-Ching / Human Design Events
# ============================================================================
# Triggered by the I-Ching Logic Kernel (Council of Systems)

MAGI_HEXAGRAM_CHANGE = "magi.hexagram.change"
"""Sun/Earth gates shifted to new hexagram.
Payload: {user_id: int, old_sun_gate: int, new_sun_gate: int, old_earth_gate: int,
new_earth_gate: int, sun_line: int, earth_line: int, timestamp: str}"""

MAGI_COUNCIL_SYNTHESIS = "magi.council.synthesis"
"""Council of Systems generated unified synthesis.
Payload: {user_id: int, resonance_score: float, resonance_type: str,
macro_theme: str, micro_theme: str, quest_suggestions: list}"""

MAGI_RESONANCE_SHIFT = "magi.resonance.shift"
"""Cross-system resonance level changed significantly.
Payload: {user_id: int, old_resonance: str, new_resonance: str,
elemental_profile: dict}"""


# ============================================================================
# Genesis Events
# ============================================================================
# Triggered by Genesis uncertainty refinement system

GENESIS_UNCERTAINTY_DECLARED = "genesis.uncertainty.declared"
"""Module declared uncertainties. Payload: GenesisUncertaintyPayload"""

GENESIS_REFINEMENT_REQUESTED = "genesis.refinement.requested"
"""Refinement probe ready. Payload: {user_id: int, session_id: str, field: str, strategy: str, probe_question: str}"""

GENESIS_CONFIDENCE_UPDATED = "genesis.confidence.updated"
"""Field confidence changed.
Payload: {user_id: int, field: str, module: str, old_confidence: float,
new_confidence: float}"""

GENESIS_FIELD_CONFIRMED = "genesis.field.confirmed"
"""Field reached confirmation threshold. Payload: GenesisFieldConfirmedPayload"""


# ============================================================================
# Hypothesis Events (Theories)
# ============================================================================
# Triggered by Hypothesis module for general theories

HYPOTHESIS_GENERATED = "hypothesis.generated"
"""Theory hypothesis generated. Payload: HypothesisGeneratedPayload"""

HYPOTHESIS_CONFIRMED = "hypothesis.confirmed"
"""Theory hypothesis confirmed. Payload: HypothesisConfirmedPayload"""

HYPOTHESIS_UPDATED = "hypothesis.confidence.updated"
"""Theory hypothesis confidence updated. Payload: HypothesisUpdatedPayload"""

HYPOTHESIS_THRESHOLD_CROSSED = "hypothesis.threshold.crossed"
"""
Hypothesis crossed a significance threshold (e.g., from FORMING to TESTING).
Payload: {
    user_id: int,
    hypothesis_id: str,
    hypothesis_type: str,
    threshold_type: str,  # 'testing_entered', 'confirmed_entered', 'testing_exited'
    old_confidence: float,
    new_confidence: float,
    old_status: str,
    new_status: str,
    evidence_id: str | None
}
"""

HYPOTHESIS_REJECTED = "hypothesis.rejected"
"""
Hypothesis rejected due to contradictory evidence.
Payload: {
    user_id: int,
    hypothesis_id: str,
    hypothesis_type: str,
    claim: str,
    final_confidence: float,
    contradiction_count: int,
    rejection_reason: str,
    timestamp: str
}
"""

HYPOTHESIS_STALE = "hypothesis.stale"
"""
Hypothesis marked stale due to lack of new evidence.
Payload: {
    user_id: int,
    hypothesis_id: str,
    hypothesis_type: str,
    claim: str,
    days_since_evidence: int,
    last_evidence_at: str | None,
    timestamp: str
}
"""

HYPOTHESIS_EVIDENCE_ADDED = "hypothesis.evidence.added"
"""
New evidence added to hypothesis.
Payload: {
    user_id: int,
    hypothesis_id: str,
    evidence_id: str,
    evidence_type: str,
    source: str,
    weight: float,
    is_contradiction: bool,
    confidence_before: float,
    confidence_after: float,
    timestamp: str
}
"""


# ============================================================================
# Cyclical Pattern Events
# ============================================================================
# Triggered by Observer cyclical pattern detection

CYCLICAL_PATTERN_DETECTED = "observer.cyclical.detected"
"""
New cyclical pattern detected aligned with magi periods.
Payload: {
    user_id: int,
    pattern_id: str,
    pattern_type: str,  # 'period_specific_symptom', 'inter_period_mood_variance', etc.
    planet: str | None,
    planet_high: str | None,
    planet_low: str | None,
    symptom: str | None,
    metric: str | None,
    confidence: float,
    p_value: float | None,
    supporting_periods: int,
    finding: str,
    spawned_hypothesis_id: str | None,
    timestamp: str
}
"""

CYCLICAL_PATTERN_CONFIRMED = "observer.cyclical.confirmed"
"""
Cyclical pattern confirmed with additional supporting periods.
Payload: {
    user_id: int,
    pattern_id: str,
    pattern_type: str,
    planet: str | None,
    old_confidence: float,
    new_confidence: float,
    old_supporting_periods: int,
    new_supporting_periods: int,
    timestamp: str
}
"""

CYCLICAL_PATTERN_EVOLUTION = "observer.cyclical.evolution"
"""
Cross-year evolution pattern detected (trend over multiple years).
Payload: {
    user_id: int,
    pattern_id: str,
    planet: str,
    metric: str,
    trend_direction: str,  # 'increasing', 'decreasing', 'stable'
    slope: float,
    r_squared: float,
    years_tracked: int,
    finding: str,
    timestamp: str
}
"""

CYCLICAL_THEME_ALIGNMENT = "observer.cyclical.theme_alignment"
"""
Journal content aligns with magi period themes.
Payload: {
    user_id: int,
    pattern_id: str,
    planet: str,
    period_theme: str,
    alignment_score: float,
    supporting_periods: int,
    finding: str,
    timestamp: str
}
"""


# ============================================================================
# Memory Events
# ============================================================================
# Triggered by Active Working Memory system

MEMORY_SYNTHESIS_CACHED = "memory.synthesis.cached"
"""Master synthesis stored in hot memory. Payload: {user_id: int, modules_included: list, themes: list}"""

MEMORY_CONTEXT_RETRIEVED = "memory.context.retrieved"
"""Full context assembled from memory. Payload: {user_id: int, has_synthesis: bool, module_count: int}"""

MEMORY_CACHE_INVALIDATED = "memory.cache.invalidated"
"""Cache entry invalidated. Payload: {user_id: int, cache_type: str, module: str | None}"""


# ============================================================================
# Progression & Evolution Events
# ============================================================================
# Triggered by the Quest and Progression Engine

QUEST_COMPLETED = "quest.completed"
"""Quest log completed. Payload: {quest_id: int, xp_gained: int, current_xp: int}"""

EVOLUTION_LEVEL_UP = "system.evolution.level_up"
"""User leveled up. Payload: {old_level: int, new_level: int, rank: str, activity_trace: dict}"""

PROGRESSION_EXPERIENCE_GAIN = "system.experience.gain"
"""Experience points gained. Payload: {amount: int, reason: str, category: str}"""

QUEST_CREATED = "quest.created"
"""New Quest created. Payload: {quest_id: int, user_id: int, title: str}"""

QUEST_REMINDER = "quest.reminder"
"""Quest reminder triggered. Payload: {quest_id: int, user_id: int, title: str}"""

REFLECTION_PROMPT_GENERATED = "insight.prompt.generated"
"""Reflection prompt generated. Payload: {prompt_id: int, user_id: int, topic: str}"""


# ============================================================================
# Journal Events
# ============================================================================
# Triggered by Journal interactions

JOURNAL_ENTRY_CREATED = "journal.entry.created"
"""New Journal Entry created. Payload: {entry_id: int, user_id: int, title: str, source: str}"""
