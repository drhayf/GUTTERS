"""
GUTTERS Numerology Interpreter - BRAIN

LLM-driven interpretation of numerology charts with practical,
empowering insights about life path and purpose.
"""
from typing import Optional


class NumerologyInterpreter:
    """LLM-driven interpretation of numerology charts"""
    
    SYSTEM_PROMPT = """You are a compassionate numerology expert providing practical, empowering insights.

Your interpretations should:
1. Explain numbers through real-life scenarios and patterns
2. Balance gifts (strengths) with challenges (growth edges)
3. Offer actionable guidance for alignment
4. Avoid fortune-telling or absolutes
5. Connect numbers to personality, relationships, and life purpose
6. Use conversational, warm language

Avoid:
- Mystical jargon without explanation
- Fatalistic predictions
- Overwhelm with too much information
- Comparison between numbers (no number is "better")

You're a wise interpreter, not a fortune teller."""
    
    # Number meanings for basic interpretation
    NUMBER_MEANINGS = {
        1: {"theme": "Independence & Leadership", "gifts": "Pioneer, innovative, self-starter", "challenges": "Ego, isolation, stubbornness"},
        2: {"theme": "Partnership & Harmony", "gifts": "Diplomatic, intuitive, supportive", "challenges": "Over-sensitivity, indecision, dependency"},
        3: {"theme": "Expression & Creativity", "gifts": "Artistic, communicative, joyful", "challenges": "Scattered, superficial, moody"},
        4: {"theme": "Foundation & Structure", "gifts": "Practical, reliable, disciplined", "challenges": "Rigid, workaholic, resistant to change"},
        5: {"theme": "Freedom & Adventure", "gifts": "Versatile, adaptable, curious", "challenges": "Restless, impulsive, scattered"},
        6: {"theme": "Nurturing & Responsibility", "gifts": "Caring, harmonious, artistic", "challenges": "Self-sacrificing, controlling, perfectionist"},
        7: {"theme": "Wisdom & Introspection", "gifts": "Analytical, spiritual, truth-seeking", "challenges": "Isolated, secretive, overly critical"},
        8: {"theme": "Power & Abundance", "gifts": "Ambitious, executive, material mastery", "challenges": "Workaholic, materialistic, controlling"},
        9: {"theme": "Humanitarianism & Completion", "gifts": "Compassionate, wise, universal love", "challenges": "Detached, scattered, martyr complex"},
        11: {"theme": "Master Intuition", "gifts": "Visionary, inspirational, highly intuitive", "challenges": "Nervous energy, impractical, overwhelmed"},
        22: {"theme": "Master Builder", "gifts": "Manifests big dreams, practical visionary", "challenges": "Overwhelmed by potential, self-doubt"},
        33: {"theme": "Master Teacher", "gifts": "Healer, uplifter, selfless service", "challenges": "Self-sacrifice, taking on others' burdens"},
    }
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def interpret_chart(
        self,
        chart,
        user_query: Optional[str] = None
    ) -> str:
        """Generate personalized interpretation"""
        from ..schemas import NumerologyChart
        
        if self.llm is None:
            return self._interpret_basic(chart)
        
        return await self._interpret_full(chart, user_query)
    
    def _interpret_basic(self, chart) -> str:
        """Basic interpretation without LLM"""
        lp = self.NUMBER_MEANINGS.get(chart.life_path, {})
        exp = self.NUMBER_MEANINGS.get(chart.expression, {})
        su = self.NUMBER_MEANINGS.get(chart.soul_urge, {})
        pers = self.NUMBER_MEANINGS.get(chart.personality, {})
        
        master_note = ""
        if chart.master_numbers:
            master_note = f"\n\n**Master Numbers:** {', '.join(map(str, chart.master_numbers))} - You carry heightened potential and responsibility."
        
        karmic_note = ""
        if chart.karmic_debt_numbers:
            karmic_note = f"\n\n**Karmic Lessons:** {', '.join(map(str, chart.karmic_debt_numbers))} - Areas for growth and integration."
        
        return f"""**Your Numerology Chart**

**Life Path: {chart.life_path}** - {lp.get('theme', 'Your Core Purpose')}
*Gifts:* {lp.get('gifts', 'Natural strengths')}
*Challenges:* {lp.get('challenges', 'Growth areas')}

**Expression: {chart.expression}** - {exp.get('theme', 'How You Express')}
*Gifts:* {exp.get('gifts', 'Natural talents')}

**Soul Urge: {chart.soul_urge}** - {su.get('theme', 'Inner Desires')}
What truly fulfills you at the deepest level.

**Personality: {chart.personality}** - {pers.get('theme', 'First Impressions')}
How others perceive you.

**Birthday: {chart.birthday}** - A special gift you were born with.{master_note}{karmic_note}"""
    
    async def _interpret_full(self, chart, user_query: Optional[str]) -> str:
        """Full interpretation with LLM"""
        from langchain_core.messages import SystemMessage, HumanMessage
        
        context = user_query if user_query else "Provide a comprehensive overview"
        
        # Build special notes
        special_notes = []
        if chart.is_master_life_path:
            special_notes.append(f"Master Life Path {chart.life_path} - heightened potential and responsibility")
        if chart.karmic_debt_numbers:
            special_notes.append(f"Karmic Debt: {', '.join(map(str, chart.karmic_debt_numbers))} - lessons to integrate")
        
        lp = self.NUMBER_MEANINGS.get(chart.life_path, {})
        exp = self.NUMBER_MEANINGS.get(chart.expression, {})
        
        prompt = f"""Interpret this numerology chart with warmth and practical wisdom.

**Chart Data:**
- Life Path: {chart.life_path}{"*" if chart.is_master_life_path else ""} - {lp.get('theme', 'Core Purpose')}
- Expression: {chart.expression} - {exp.get('theme', 'Natural Expression')}
- Soul Urge: {chart.soul_urge} - Inner desires and motivations
- Personality: {chart.personality} - Outer persona, first impression
- Birthday: {chart.birthday} - Natural gifts from birth day

**Special Notes:**
{chr(10).join(special_notes) if special_notes else "None"}

**User Context:** {context}

**Instructions:**
1. Start with their Life Path - what they're here to learn/do
2. Explain how their Expression supports their Life Path
3. Describe their Soul Urge - what truly fulfills them
4. Discuss their Personality - how they show up in the world
5. Show how these numbers work together or create tension
6. If master numbers: explain heightened gifts and challenges
7. If karmic debt: explain the lesson with compassion
8. End with practical guidance for living in alignment

Keep it conversational (700-1000 words). Use specific examples. Balance light and shadow."""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        return response.content
