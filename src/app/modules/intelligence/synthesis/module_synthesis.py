"""
Module-specific synthesis generators.

Each calculation module generates its own narrative contribution
before being combined into master synthesis.
"""

from typing import Optional, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

class ModuleSynthesizer:
    """Generate module-specific synthesis from module data."""
    
    def __init__(self, llm):
        self.llm = llm
    
    async def synthesize_astrology(self, astro_data: Dict[str, Any]) -> str:
        """
        Generate narrative synthesis from astrology data.
        
        Args:
            astro_data: Complete natal chart + transits
        
        Returns:
            Narrative string focusing on astrological insights
        """
        if not astro_data:
            return ""
        
        # Extract key placements
        sun_sign = astro_data.get('sun', {}).get('sign', 'Unknown')
        moon_sign = astro_data.get('moon', {}).get('sign', 'Unknown')
        rising_sign = astro_data.get('rising_sign', 'Unknown')
        
        # Build focused prompt
        prompt = f"""Generate a concise astrological synthesis (3-4 sentences) for this natal chart:

**Sun:** {sun_sign}
**Moon:** {moon_sign}
**Rising:** {rising_sign}

Focus on:
1. Core identity and life purpose (Sun)
2. Emotional nature and needs (Moon)
3. Outer persona and approach to life (Rising)

Write in second person ("You are..."). Be specific and insightful, not generic."""
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are an expert astrologer creating personalized insights."),
            HumanMessage(content=prompt)
        ])
        
        return response.content.strip()
    
    async def synthesize_human_design(self, hd_data: Dict[str, Any]) -> str:
        """Generate narrative synthesis from Human Design data."""
        if not hd_data:
            return ""
        
        design_type = hd_data.get('type', 'Unknown')
        strategy = hd_data.get('strategy', 'Unknown')
        authority = hd_data.get('authority', 'Unknown')
        
        prompt = f"""Generate a concise Human Design synthesis (3-4 sentences):

**Type:** {design_type}
**Strategy:** {strategy}
**Authority:** {authority}

Focus on:
1. How this person operates best
2. Decision-making approach
3. Energy dynamics

Write in second person. Be practical and actionable."""
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a Human Design expert."),
            HumanMessage(content=prompt)
        ])
        
        return response.content.strip()
    
    async def synthesize_numerology(self, num_data: Dict[str, Any]) -> str:
        """Generate narrative synthesis from numerology data."""
        if not num_data:
            return ""
        
        life_path = num_data.get('life_path_number', 'Unknown')
        expression = num_data.get('expression_number', 'Unknown')
        
        prompt = f"""Generate a concise numerology synthesis (2-3 sentences):

**Life Path:** {life_path}
**Expression Number:** {expression}

Focus on life themes and natural talents.
Write in second person."""
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a numerology expert."),
            HumanMessage(content=prompt)
        ])
        
        return response.content.strip()
    
    async def synthesize_observer_patterns(self, findings: list[Dict[str, Any]]) -> str:
        """
        Generate narrative from Observer findings.
        
        Args:
            findings: List of Observer pattern detections
        
        Returns:
            Narrative explaining detected patterns
        """
        if not findings:
            return ""
        
        # Format findings for LLM
        findings_text = "\n".join([
            f"- {f['finding']} (confidence: {f['confidence']:.0%})"
            for f in findings[:5]  # Top 5
        ])
        
        prompt = f"""Generate a cohesive narrative (4-5 sentences) from these detected patterns:

{findings_text}

Explain:
1. What patterns have been observed
2. What these patterns reveal about the person
3. Practical implications

Write in second person ("Your patterns show..."). Be specific, not generic."""
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a pattern analysis expert."),
            HumanMessage(content=prompt)
        ])
        
        return response.content.strip()
