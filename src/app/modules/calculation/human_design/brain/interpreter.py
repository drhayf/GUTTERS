"""
GUTTERS Human Design Interpreter - BRAIN

LLM-driven interpretation of Human Design charts with somatic, trauma-informed insights.
"""
from typing import Optional


class HumanDesignInterpreter:
    """LLM-driven interpretation of Human Design charts"""
    
    SYSTEM_PROMPT = """You are a compassionate Human Design expert providing somatic, trauma-informed insights.

Your interpretations should:
1. Use warm, embodied language (not clinical)
2. Explain concepts through felt experience and daily scenarios
3. Balance light (gifts) with shadow (challenges)
4. Avoid spiritual bypassing - acknowledge real struggles
5. Offer practical, actionable guidance
6. Connect HD concepts to nervous system states and body wisdom
7. Use "you might notice..." rather than absolute statements

Avoid:
- Rigid rules or absolutes
- Spiritual hierarchy (no type is "better")
- Overwhelming with jargon
- Bypassing real pain with platitudes

You're a wise guide, not a guru."""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def interpret_chart(
        self,
        chart,
        user_query: Optional[str] = None
    ) -> str:
        """Generate personalized interpretation"""
        from ..schemas import HumanDesignChart
        
        if chart.accuracy == "partial":
            return self._interpret_partial(chart, user_query)
        
        if self.llm is None:
            return self._interpret_basic(chart)
        
        return await self._interpret_full(chart, user_query)
    
    def _interpret_partial(self, chart, user_query: Optional[str]) -> str:
        """Interpret partial chart (no birth time)"""
        return f"""**Your Human Design - Partial Reading**

Based on your birth date alone, you appear to be a **{chart.type}**.

**{chart.type}s** are designed to {chart.strategy.lower()}. This isn't a personality trait - it's about how your energy field naturally operates.

**Note:** Without your exact birth time, I can't show you:
- Your full bodygraph (centers, channels, gates)
- Your Profile (life theme)
- Your Incarnation Cross (life purpose)
- Precise Authority (decision-making strategy)

**What this means:** The Type is a strong indicator, but for the complete picture - including how you make decisions and what your life purpose is - we'd need your birth time.

If you can find your birth time (check birth certificate, hospital records, or ask family), I can generate your complete chart.

For now: As a {chart.type}, notice how your energy responds to opportunities. {chart.strategy} might feel counterintuitive to conditioning, but it's your natural rhythm."""
    
    def _interpret_basic(self, chart) -> str:
        """Basic interpretation without LLM"""
        defined = ', '.join(chart.defined_centers) if chart.defined_centers else 'None'
        undefined = ', '.join(chart.undefined_centers) if chart.undefined_centers else 'None'
        
        defined_channels = [c for c in chart.channels if c.defined]
        channel_text = ', '.join([c.name for c in defined_channels]) if defined_channels else 'None'
        
        return f"""**Your Human Design Chart**

**Type:** {chart.type}
**Strategy:** {chart.strategy}
**Authority:** {chart.authority}
**Profile:** {chart.profile}
**Incarnation Cross:** {chart.incarnation_cross}

**Defined Centers:** {defined}
**Undefined Centers:** {undefined}

**Defined Channels:** {channel_text}

---

**As a {chart.type}**, your strategy is to {chart.strategy.lower()}. This is how your energy works best.

**Your Authority ({chart.authority})** guides your decision-making. Trust this inner guidance system.

**Profile {chart.profile}** describes your life theme and how you interact with the world."""
    
    async def _interpret_full(self, chart, user_query: Optional[str]) -> str:
        """Full interpretation with LLM"""
        from langchain_core.messages import SystemMessage, HumanMessage
        
        context = user_query if user_query else "Provide a comprehensive overview of this person's design"
        
        prompt = f"""Interpret this Human Design chart with warmth and somatic depth.

**Chart Data:**
- Type: {chart.type}
- Strategy: {chart.strategy}
- Authority: {chart.authority}
- Profile: {chart.profile}
- Defined Centers: {', '.join(chart.defined_centers)}
- Undefined Centers: {', '.join(chart.undefined_centers)}
- Key Gates: {', '.join([f"{g.gate}.{g.line}" for g in chart.personality_gates[:4]])}
- Incarnation Cross: {chart.incarnation_cross}

**User Context:** {context}

**Instructions:**
1. Start with their Type and what that means for their energy
2. Explain their Strategy in practical daily terms
3. Describe their Authority - how they make best decisions
4. Interpret their Profile as a life theme
5. Discuss their defined centers as consistent energy
6. Discuss their undefined centers as where they absorb others' energy
7. End with one embodied practice aligned with their design

Keep it conversational (800-1200 words). Use "you might notice..." framing. Balance gifts with challenges. Be specific to THIS chart."""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        return response.content
