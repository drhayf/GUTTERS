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


# ============================================================================
# Genesis Events
# ============================================================================
# Triggered by Genesis uncertainty refinement system

GENESIS_UNCERTAINTY_DECLARED = "genesis.uncertainty.declared"
"""Module declared uncertainties. Payload: GenesisUncertaintyPayload"""

GENESIS_REFINEMENT_REQUESTED = "genesis.refinement.requested"
"""Refinement probe ready. Payload: {user_id: int, session_id: str, field: str, strategy: str, probe_question: str}"""

GENESIS_CONFIDENCE_UPDATED = "genesis.confidence.updated"
"""Field confidence changed. Payload: {user_id: int, field: str, module: str, old_confidence: float, new_confidence: float}"""

GENESIS_FIELD_CONFIRMED = "genesis.field.confirmed"
"""Field reached confirmation threshold. Payload: GenesisFieldConfirmedPayload"""

