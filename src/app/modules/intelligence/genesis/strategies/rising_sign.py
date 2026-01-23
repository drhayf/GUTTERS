"""
Rising Sign Refinement Strategies

Strategies for refining rising sign uncertainty through conversation.
"""

from ..probes import ProbeType
from ..hypothesis import Hypothesis


class MorningRoutineStrategy:
    """Probe based on morning energy patterns."""
    
    strategy_name = "morning_routine"
    applicable_fields = ["rising_sign"]
    probe_type = ProbeType.BINARY_CHOICE
    
    # Rising signs grouped by morning patterns
    EARLY_RISERS = {"Aries", "Capricorn", "Virgo", "Leo"}
    SLOW_STARTERS = {"Pisces", "Taurus", "Cancer", "Libra"}
    VARIABLE = {"Gemini", "Sagittarius", "Scorpio", "Aquarius"}
    
    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        return f"""Generate a binary choice question about morning routines to help identify rising sign.

We're testing if this person's rising sign might be {hypothesis.suspected_value}.

Rising sign associations:
- Early risers (jump right in): Aries, Capricorn, Virgo, Leo
- Slow starters (ease into day): Pisces, Taurus, Cancer, Libra
- Variable: Gemini, Sagittarius, Scorpio, Aquarius

{hypothesis.suspected_value} rising typically: {self._get_characteristic(hypothesis.suspected_value)}

Requirements:
- Ask about morning preferences/habits
- Two clear options
- Warm, curious tone
- Don't mention astrology

Return JSON:
{{
    "question": "When you wake up, do you...",
    "options": ["Option A", "Option B"],
    "mappings": {{
        "0": {{"sign1": 0.15, "sign2": 0.10}},
        "1": {{"sign3": 0.15, "sign4": 0.10}}
    }}
}}"""
    
    def _get_characteristic(self, sign: str) -> str:
        if sign in self.EARLY_RISERS:
            return "jumps into action, productive early"
        elif sign in self.SLOW_STARTERS:
            return "eases into the day, needs transition time"
        else:
            return "varies based on what's planned"


class FirstImpressionStrategy:
    """Probe based on how others perceive them initially."""
    
    strategy_name = "first_impression"
    applicable_fields = ["rising_sign"]
    probe_type = ProbeType.REFLECTION
    
    IMPRESSIONS = {
        "Aries": "confident, direct, energetic",
        "Taurus": "calm, reliable, grounded",
        "Gemini": "curious, talkative, witty",
        "Cancer": "nurturing, protective, warm",
        "Leo": "charismatic, warm, commanding",
        "Virgo": "refined, helpful, observant",
        "Libra": "charming, graceful, diplomatic",
        "Scorpio": "intense, mysterious, magnetic",
        "Sagittarius": "adventurous, optimistic, friendly",
        "Capricorn": "serious, capable, reserved",
        "Aquarius": "unique, friendly, intellectual",
        "Pisces": "dreamy, empathetic, gentle",
    }
    
    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        return f"""Generate a reflection question about first impressions.

We're testing if rising sign is {hypothesis.suspected_value}.
{hypothesis.suspected_value} rising typically comes across as: {self.IMPRESSIONS.get(hypothesis.suspected_value, "unique")}

Ask them how people typically describe meeting them for the first time. Keep it warm and curious.

Return JSON:
{{
    "question": "How do people usually describe their first impression of meeting you?",
    "analysis_hints": {{
        "confident_assertive": ["Aries", "Leo", "Capricorn"],
        "warm_nurturing": ["Cancer", "Pisces", "Libra"],
        "analytical_reserved": ["Virgo", "Scorpio", "Aquarius"],
        "friendly_adventurous": ["Sagittarius", "Gemini", "Aries"],
        "calm_grounded": ["Taurus", "Capricorn", "Virgo"]
    }}
}}"""


class LifeEventTimingStrategy:
    """Probe based on significant life event timing."""
    
    strategy_name = "life_event_timing"
    applicable_fields = ["rising_sign"]
    probe_type = ProbeType.REFLECTION
    
    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        return f"""Generate a question about when major life events tend to happen.

We're testing if rising sign is {hypothesis.suspected_value}.
Rising sign can influence when significant events (career changes, relationships, moves) tend to occur.

Keep it open-ended and conversational.

Return JSON:
{{
    "question": "Think of a few major turning points in your life - starting a career, big relationship changes, moving. Do you notice any patterns in when these tend to happen?",
    "analysis_hints": {{
        "spring_march_april": ["Aries"],
        "late_spring_may": ["Taurus"],
        "early_summer_june": ["Gemini"],
        "summer_july": ["Cancer"],
        "late_summer_august": ["Leo"],
        "early_fall_september": ["Virgo"],
        "fall_october": ["Libra"],
        "late_fall_november": ["Scorpio"],
        "early_winter_december": ["Sagittarius"],
        "mid_winter_january": ["Capricorn"],
        "late_winter_february": ["Aquarius"],
        "early_spring_march": ["Pisces"]
    }}
}}"""


class PhysicalAppearanceStrategy:
    """Confirmation based on rising sign physical traits."""
    
    strategy_name = "physical_appearance"
    applicable_fields = ["rising_sign"]
    probe_type = ProbeType.CONFIRMATION
    
    TRAITS = {
        "Aries": "athletic build, prominent forehead, direct gaze",
        "Taurus": "sturdy build, strong neck, calm presence",
        "Gemini": "quick movements, expressive hands, youthful look",
        "Cancer": "rounded features, nurturing presence",
        "Leo": "strong posture, expressive features, mane-like hair",
        "Virgo": "refined features, neat appearance, observant eyes",
        "Libra": "balanced features, graceful movements, pleasant smile",
        "Scorpio": "intense eyes, magnetic presence, strong jawline",
        "Sagittarius": "athletic, open expression, tall or leggy",
        "Capricorn": "defined bone structure, mature presence",
        "Aquarius": "unique style, friendly expression, unusual features",
        "Pisces": "soft features, dreamy eyes, fluid movements",
    }
    
    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        traits = self.TRAITS.get(hypothesis.suspected_value, "distinct presence")
        return f"""Generate a confirmation question about physical traits.

We're testing if rising sign is {hypothesis.suspected_value}.
{hypothesis.suspected_value} rising often has: {traits}

Ask if these traits resonate, but phrase it naturally.

Return JSON:
{{
    "question": "Some people have mentioned you have [trait description]. Does that resonate with how you or others see you?",
    "mappings": {{
        "yes": {{"{hypothesis.suspected_value}": 0.20}},
        "no": {{"{hypothesis.suspected_value}": -0.10}}
    }}
}}"""
