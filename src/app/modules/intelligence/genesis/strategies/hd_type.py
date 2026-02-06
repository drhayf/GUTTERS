"""
Human Design Type Refinement Strategies

Strategies for refining HD type uncertainty through conversation.
"""

from ..hypothesis import Hypothesis
from ..probes import ProbeType


class EnergyPatternStrategy:
    """Probe based on daily energy patterns."""

    strategy_name = "energy_pattern"
    applicable_fields = ["type"]
    probe_type = ProbeType.BINARY_CHOICE

    ENERGY_PATTERNS = {
        "Generator": "consistent regenerating energy when doing work they love",
        "Manifesting Generator": "bursts of multi-passionate energy, needs variety",
        "Projector": "bursts of effectiveness, needs significant rest",
        "Manifestor": "initiating spurts, needs to retreat after big pushes",
        "Reflector": "fluctuating with the lunar cycle, needs sampling time",
    }

    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        pattern = self.ENERGY_PATTERNS.get(hypothesis.suspected_value, "unique pattern")
        return f"""Generate a binary choice question about energy patterns.

We're testing if HD type is {hypothesis.suspected_value}.
{hypothesis.suspected_value}s typically have: {pattern}

Types grouped by energy:
- Sustainable energy: Generator, Manifesting Generator
- Strategic energy: Projector
- Initiating energy: Manifestor
- Variable energy: Reflector

Ask about their typical energy experience throughout the day.

Return JSON:
{{
    "question": "When it comes to your daily energy, do you...",
    "options": ["Option describing one pattern", "Option describing another pattern"],
    "mappings": {{
        "0": {{"Generator": 0.15, "Manifesting Generator": 0.12}},
        "1": {{"Projector": 0.18, "Manifestor": 0.08}}
    }}
}}"""


class DecisionStyleStrategy:
    """Probe based on how they make decisions."""

    strategy_name = "decision_style"
    applicable_fields = ["type", "authority"]
    probe_type = ProbeType.BINARY_CHOICE

    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        return f"""Generate a binary choice question about decision-making style.

We're testing if HD type is {hypothesis.suspected_value}.

Decision patterns by type:
- Generator/MG: Wait for gut response, satisfaction-based
- Projector: Wait for recognition/invitation, success-based
- Manifestor: Initiate, inform others, peace-based
- Reflector: Sample over time, surprise-based

Ask about how they approach important decisions.

Return JSON:
{{
    "question": "When faced with a big decision, do you typically...",
    "options": ["Act on a gut feeling that arises", "Wait until you feel recognized or invited"],
    "mappings": {{
        "0": {{"Generator": 0.15, "Manifesting Generator": 0.15, "Manifestor": 0.08}},
        "1": {{"Projector": 0.20, "Reflector": 0.10}}
    }}
}}"""


class WaitingResponseStrategy:
    """Probe based on initiating vs responding tendency."""

    strategy_name = "waiting_response"
    applicable_fields = ["type"]
    probe_type = ProbeType.CONFIRMATION

    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        is_responder = hypothesis.suspected_value in {"Generator", "Manifesting Generator"}
        is_initiator = hypothesis.suspected_value == "Manifestor"

        if is_responder:
            focus = "wait for something to respond to rather than initiating"
        elif is_initiator:
            focus = "initiate and inform others rather than waiting"
        else:
            focus = "wait to be recognized or invited before engaging"

        return f"""Generate a confirmation question about responding vs initiating.

We're testing if type is {hypothesis.suspected_value}.
{hypothesis.suspected_value}s typically: {focus}

Ask if this pattern resonates with their life experience.

Return JSON:
{{
    "question": "Looking at your life, do you find things work better when you [pattern description]?",
    "mappings": {{
        "yes": {{"{hypothesis.suspected_value}": 0.20}},
        "no": {{"{hypothesis.suspected_value}": -0.15}}
    }}
}}"""


class WorkRhythmStrategy:
    """Probe based on sustainable work patterns."""

    strategy_name = "work_rhythm"
    applicable_fields = ["type"]
    probe_type = ProbeType.SLIDER

    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        return f"""Generate a slider question (1-10) about work sustainability.

We're testing if type is {hypothesis.suspected_value}.

Work patterns:
- Generators/MGs (1-4): Can work long hours when engaged, need to love the work
- Projectors/Manifestors (5-7): Need significant downtime, bursts of productivity
- Reflectors (8-10): Need varied rhythm, shouldn't follow consistent schedule

Ask them to rate how much rest/downtime they need to function well.

Return JSON:
{{
    "question": (
        "On a scale of 1-10, how much rest and downtime do you need between "
        "periods of work? (1=minimal, can work endlessly; 10=significant, need "
        "lots of recovery)"
    ),
    "mappings": {{
        "low": {{"Generator": 0.15, "Manifesting Generator": 0.12}},
        "mid": {{"Projector": 0.18, "Manifestor": 0.15}},
        "high": {{"Reflector": 0.20, "Projector": 0.08}}
    }}
}}"""


class SocialInteractionStrategy:
    """Probe based on social interaction patterns."""

    strategy_name = "social_interaction"
    applicable_fields = ["type"]
    probe_type = ProbeType.BINARY_CHOICE

    def generate_prompt(self, hypothesis: Hypothesis) -> str:
        return f"""Generate a binary choice about social interactions.

We're testing if type is {hypothesis.suspected_value}.

Social patterns:
- Generators/MGs: Magnetic, people drawn to their energy, respond to invitations
- Projectors: Need to wait for recognition, can feel invisible until seen
- Manifestors: Natural initiators, inform others of plans
- Reflectors: Mirror others, need to sample people before connecting

Ask about their social experience.

Return JSON:
{{
    "question": "In social situations, do you typically...",
    "options": [
        "Feel like people are naturally drawn to you/your energy",
        "Feel like you need to be recognized or invited before you can fully engage"
    ],
    "mappings": {{
        "0": {{"Generator": 0.15, "Manifesting Generator": 0.12, "Manifestor": 0.08}},
        "1": {{"Projector": 0.20, "Reflector": 0.10}}
    }}
}}"""
