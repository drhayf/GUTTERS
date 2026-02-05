from pydantic import BaseModel
from typing import Callable, Optional


class NotificationConfig(BaseModel):
    preference_key: str  # The key in UserProfile.data['preferences']['notifications']
    title_template: str
    body_template: str
    deep_link: str = "/"
    filter_func: Optional[Callable[[dict], bool]] = None  # Optional logic (e.g., check Kp > 5)


# Filter Logic Helpers
def needs_high_kp(payload: dict) -> bool:
    return payload.get("kp_index", 0) >= 5 or "Storm" in payload.get("kp_status", "")


def needs_significant_moon(payload: dict) -> bool:
    phase = payload.get("moon_phase", "").lower()
    return "new" in phase or "full" in phase


def is_outer_planet(payload: dict) -> bool:
    """Filter for outer planet events (more significant)."""
    planet = payload.get("planet", "").lower()
    return planet in ["mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]


# The Declarative Map
# Event Type -> Config
EVENT_MAP: dict[str, NotificationConfig] = {
    # =========================================================================
    # SOLAR TRACKING EVENTS
    # =========================================================================
    "cosmic.solar.alert": NotificationConfig(
        preference_key="solar_alerts",
        title_template="⚡ Solar Alert: {event_name}",
        body_template="Shield Status: {shield_integrity}. Kp Index: {kp_index}.",
        deep_link="/tracking?tab=solar",
    ),
    "cosmic.storm.detected": NotificationConfig(
        preference_key="solar_alerts",
        title_template="🌩️ Geomagnetic Storm Detected",
        body_template="Kp Index has reached {kp_index}. {severity} conditions.",
        deep_link="/tracking?tab=solar",
        filter_func=needs_high_kp,
    ),
    "cosmic.aurora.alert": NotificationConfig(
        preference_key="solar_alerts",
        title_template="🌌 Aurora Alert: {aurora_status}",
        body_template="Aurora {probability:.0%} probability at your latitude. {viewing_direction}",
        deep_link="/tracking?tab=solar",
        filter_func=lambda p: p.get("probability", 0) >= 0.3,
    ),
    "cosmic.geomagnetic.impact": NotificationConfig(
        preference_key="solar_alerts",
        title_template="🧭 Local Geomagnetic Impact: {severity}",
        body_template="Your location ({geomag_lat:.1f}° geomag) is experiencing {severity} effects.",
        deep_link="/tracking?tab=solar",
        filter_func=lambda p: p.get("severity_level", 0) >= 2,
    ),

    # =========================================================================
    # LUNAR TRACKING EVENTS
    # =========================================================================
    "cosmic.lunar.voc_start": NotificationConfig(
        preference_key="lunar_voc",
        title_template="🌙 Void of Course Begins",
        body_template="Moon enters void in {moon_sign}. Duration: ~{duration_hours:.1f}h. Avoid new beginnings.",
        deep_link="/tracking?tab=lunar",
    ),
    "cosmic.lunar.voc_end": NotificationConfig(
        preference_key="lunar_voc",
        title_template="✨ Void of Course Ends",
        body_template="Moon enters {new_sign}. Energy shifts. Good time for new actions.",
        deep_link="/tracking?tab=lunar",
    ),
    "cosmic.lunar.phase": NotificationConfig(
        preference_key="lunar_phases",
        title_template="🌕 {phase_name} in {moon_sign}",
        body_template="Significant lunar gateway. Illumination: {illumination:.0%}.",
        deep_link="/tracking?tab=lunar",
        filter_func=needs_significant_moon,
    ),
    "cosmic.full_moon": NotificationConfig(
        preference_key="lunar_phases",
        title_template="🌕 Full Moon in {sign}",
        body_template="Peak illumination. Time for release and clarity.",
        deep_link="/tracking?tab=lunar",
    ),

    # =========================================================================
    # TRANSIT/RETROGRADE EVENTS
    # =========================================================================
    "cosmic.retrograde.start": NotificationConfig(
        preference_key="retrograde_alerts",
        title_template="↩️ {planet} Retrograde Begins",
        body_template="{planet} stations retrograde in {sign}. Review and reflect themes for ~{duration_days} days.",
        deep_link="/tracking?tab=transits",
        filter_func=is_outer_planet,  # Only notify for outer planets by default
    ),
    "cosmic.retrograde.end": NotificationConfig(
        preference_key="retrograde_alerts",
        title_template="➡️ {planet} Goes Direct",
        body_template="{planet} stations direct in {sign}. Forward momentum resumes.",
        deep_link="/tracking?tab=transits",
        filter_func=is_outer_planet,
    ),
    "cosmic.planet.station": NotificationConfig(
        preference_key="retrograde_alerts",
        title_template="⚠️ {planet} Stationing",
        body_template="{planet} nearly stationary in {sign}. Maximum intensity ({station_type}).",
        deep_link="/tracking?tab=transits",
        filter_func=is_outer_planet,
    ),
    "cosmic.transit.exact": NotificationConfig(
        preference_key="transit_aspects",
        title_template="🎯 Transit Exact: {planet} {aspect} {natal_planet}",
        body_template="A significant transit to your natal chart is exact now.",
        deep_link="/tracking?tab=transits",
    ),
    "cosmic.ingress": NotificationConfig(
        preference_key="ingress_alerts",
        title_template="🚀 {planet} Enters {new_sign}",
        body_template="{planet} shifts from {old_sign} to {new_sign}. Energy transition.",
        deep_link="/tracking?tab=transits",
        filter_func=is_outer_planet,
    ),

    # =========================================================================
    # LEGACY / COMBINED COSMIC EVENT
    # =========================================================================
    "cosmic_update": NotificationConfig(
        preference_key="cosmic",
        title_template="Cosmic Alert: {kp_status}",
        body_template="Kp Index is {kp_index}. Moon is {moon_phase}.",
        filter_func=lambda p: needs_high_kp(p) or needs_significant_moon(p),
    ),

    # =========================================================================
    # QUESTS
    # =========================================================================
    "quest.created": NotificationConfig(
        preference_key="quests",
        title_template="📋 New Directive",
        body_template="{title}",
        deep_link="/quests",
    ),
    "quest.completed": NotificationConfig(
        preference_key="quests",
        title_template="✅ Directive Complete",
        body_template="You earned {xp_reward} XP!",
        deep_link="/quests",
    ),
    "quest.reminder": NotificationConfig(
        preference_key="quests",
        title_template="⏰ Quest Reminder",
        body_template="Don't forget: {title}",
        deep_link="/quests",
    ),

    # =========================================================================
    # EVOLUTION
    # =========================================================================
    "system.evolution.level_up": NotificationConfig(
        preference_key="evolution",
        title_template="🏆 Evolution Achieved",
        body_template="You have reached Rank {rank}!",
        deep_link="/profile",
    ),

    # =========================================================================
    # INTELLIGENCE
    # =========================================================================
    "hypothesis.updated": NotificationConfig(
        preference_key="intelligence",
        title_template="🧠 Pattern Detected",
        body_template="My understanding of '{trait}' has evolved.",
        deep_link="/journal",
    ),
    "synthesis.generated": NotificationConfig(
        preference_key="intelligence",
        title_template="✨ New Profile Synthesis",
        body_template="A new reflection on your data is available.",
        deep_link="/profile",
    ),

    # =========================================================================
    # COUNCIL OF SYSTEMS (I-Ching + Cardology)
    # =========================================================================
    "magi.hexagram.change": NotificationConfig(
        preference_key="magi_gates",
        title_template="🌀 Gate Transition: Gate {new_sun_gate}",
        body_template="{new_gate_name} — Gift: {new_gate_gift}",
        deep_link="/council",
        filter_func=lambda p: p.get("significance") == "major",  # Only major gate shifts
    ),
    "magi.line.shift": NotificationConfig(
        preference_key="magi_lines",
        title_template="🔄 Line Shift: Gate {new_sun_gate} Line {sun_line}",
        body_template="{line_name}: {line_keynote}",
        deep_link="/council",
    ),
    "magi.council.synthesis": NotificationConfig(
        preference_key="magi_synthesis",
        title_template="✨ Council Synthesis Available",
        body_template="Resonance: {resonance_type}. Gift: {unified_gift}",
        deep_link="/council",
    ),
    "magi.resonance.shift": NotificationConfig(
        preference_key="magi_resonance",
        title_template="⚡ Resonance Shift: {new_resonance}",
        body_template="Cross-system harmony has shifted from {old_resonance} to {new_resonance}.",
        deep_link="/council",
    ),

    # =========================================================================
    # JOURNAL
    # =========================================================================
    "journal.entry.created": NotificationConfig(
        preference_key="journal",
        title_template="📔 Journal Entry Logged",
        body_template="Entry '{title}' securely archived.",
        deep_link="/journal",
    ),
    "journal.cosmic_entry.created": NotificationConfig(
        preference_key="journal",
        title_template="🌀 Cosmic Journal Entry",
        body_template="{title}",
        deep_link="/journal",
    ),
    "insight.prompt.generated": NotificationConfig(
        preference_key="intelligence",
        title_template="💡 New Reflection",
        body_template="A new prompt about '{topic}' is available.",
        deep_link="/journal",
    ),
}
