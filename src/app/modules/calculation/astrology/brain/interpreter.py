"""
GUTTERS Astrology Interpreter - BRAIN

AI-powered natal chart interpretation.
Uses LLM to generate natural language insights from chart data.

NO event system knowledge - pure inputs and outputs.
"""
from typing import Any


async def interpret_natal_chart(
    chart: dict[str, Any],
    model_id: str = "xiaomi/mimo-v2-flash:free",
    temperature: float = 0.7,
) -> str:
    """
    Generate natural language interpretation of a natal chart.
    
    Uses LLM to synthesize chart data into meaningful insights.
    
    Args:
        chart: Natal chart data from calculate_natal_chart()
        model_id: OpenRouter model ID for interpretation
        temperature: LLM temperature (0.0-1.0)
        
    Returns:
        Natural language interpretation of the chart
        
    Example:
        >>> chart = calculate_natal_chart(...)
        >>> interpretation = await interpret_natal_chart(chart)
        >>> print(interpretation)
        "Your Sun in Taurus..."
    """
    from ....core.ai.llm_factory import get_llm
    
    # Build prompt with chart data
    prompt = _build_interpretation_prompt(chart)
    
    # Get LLM and generate interpretation
    llm = get_llm(model_id, temperature)
    response = await llm.ainvoke(prompt)
    
    return response.content


def _build_interpretation_prompt(chart: dict[str, Any]) -> str:
    """
    Build interpretation prompt from chart data.
    
    Args:
        chart: Natal chart data
        
    Returns:
        Formatted prompt for LLM
    """
    # Extract key chart elements
    planets = chart.get("planets", [])
    ascendant = chart.get("ascendant", {})
    elements = chart.get("elements", {})
    modalities = chart.get("modalities", {})
    
    # Format planet positions
    planet_lines = []
    for p in planets:
        retrograde = " (R)" if p.get("retrograde") else ""
        planet_lines.append(
            f"- {p['name']}: {p['degree']}° {p['sign']} in House {p['house']}{retrograde}"
        )
    
    prompt = f"""You are an expert astrologer providing personalized insights.

Analyze this natal chart and provide a comprehensive interpretation focusing on:
1. Core identity (Sun, Moon, Ascendant)
2. Key strengths and challenges
3. Life themes based on planetary patterns
4. Element and modality balance

CHART DATA:

Ascendant: {ascendant.get('degree', 0)}° {ascendant.get('sign', 'Unknown')}

Planetary Positions:
{chr(10).join(planet_lines)}

Element Distribution:
- Fire: {elements.get('fire', 0)} planets
- Earth: {elements.get('earth', 0)} planets
- Air: {elements.get('air', 0)} planets
- Water: {elements.get('water', 0)} planets

Modality Distribution:
- Cardinal: {modalities.get('cardinal', 0)} planets
- Fixed: {modalities.get('fixed', 0)} planets
- Mutable: {modalities.get('mutable', 0)} planets

Provide a personalized, insightful interpretation in a warm, supportive tone.
Focus on growth potential and self-understanding rather than predictions.
Keep the interpretation concise but meaningful (300-500 words).
"""
    
    return prompt


def format_chart_summary(chart: dict[str, Any]) -> str:
    """
    Create a brief text summary of the chart (no LLM).
    
    Args:
        chart: Natal chart data
        
    Returns:
        Brief text summary
    """
    planets = chart.get("planets", [])
    ascendant = chart.get("ascendant", {})
    
    # Find Sun, Moon, Ascendant
    sun = next((p for p in planets if p["name"] == "Sun"), None)
    moon = next((p for p in planets if p["name"] == "Moon"), None)
    
    sun_sign = sun["sign"] if sun else "Unknown"
    moon_sign = moon["sign"] if moon else "Unknown"
    asc_sign = ascendant.get("sign", "Unknown")
    
    return f"Sun in {sun_sign}, Moon in {moon_sign}, {asc_sign} Rising"
