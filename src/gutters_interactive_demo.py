#!/usr/bin/env python
"""
GUTTERS Interactive Demo

Complete interactive demo of the GUTTERS Intelligence Layer.
Allows you to input birth data, run all calculations, and chat with the system.

Run: python gutters_interactive_demo.py

Requires:
- OPENROUTER_API_KEY environment variable set (or .env file)
- Database connection (or will use mock data)
"""
import asyncio
import os
import sys
from datetime import date, time, datetime
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}▸ {text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'─' * 50}{Colors.ENDC}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_ai_response(text: str):
    """Print AI response in a nice format."""
    print(f"\n{Colors.CYAN}{'─' * 50}{Colors.ENDC}")
    print(f"{Colors.BOLD}AI Response:{Colors.ENDC}")
    print(text)
    print(f"{Colors.CYAN}{'─' * 50}{Colors.ENDC}\n")


class GuttersDemo:
    """Interactive demo for GUTTERS."""
    
    def __init__(self):
        self.user_data = {}
        self.profile_data = {}
        self.llm = None
        self.use_live_llm = False
        
    def check_api_key(self) -> bool:
        """Check if OpenRouter API key is available."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            print_success("OPENROUTER_API_KEY found")
            self.use_live_llm = True
            return True
        else:
            print_warning("OPENROUTER_API_KEY not found - will use template responses")
            self.use_live_llm = False
            return False
    
    def collect_birth_data(self):
        """Collect birth data from user."""
        print_section("Birth Data Collection")
        
        # Name
        name = input("Enter your name: ").strip()
        if not name:
            name = "Demo User"
        self.user_data["name"] = name
        
        # Birth date
        while True:
            date_str = input("Enter birth date (YYYY-MM-DD): ").strip()
            if not date_str:
                date_str = "1990-05-15"
                print_info(f"Using default: {date_str}")
            try:
                birth_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                self.user_data["birth_date"] = birth_date
                break
            except ValueError:
                print_error("Invalid date format. Please use YYYY-MM-DD")
        
        # Birth time
        while True:
            time_str = input("Enter birth time (HH:MM, 24hr format, or 'unknown'): ").strip()
            if not time_str:
                time_str = "12:00"
                print_info(f"Using default: {time_str}")
            if time_str.lower() == "unknown":
                self.user_data["birth_time"] = None
                print_warning("Birth time unknown - some calculations will be approximate")
                break
            try:
                birth_time = datetime.strptime(time_str, "%H:%M").time()
                self.user_data["birth_time"] = birth_time
                break
            except ValueError:
                print_error("Invalid time format. Please use HH:MM (e.g., 14:30)")
        
        # Birth location
        location = input("Enter birth location (city, country): ").strip()
        if not location:
            location = "Los Angeles, USA"
            print_info(f"Using default: {location}")
        self.user_data["birth_location"] = location
        
        # Get coordinates from geocoding
        print_info("Looking up coordinates...")
        try:
            from app.core.utils.geocoding import geocode_location
            geo_result = geocode_location(location)
            if geo_result:
                self.user_data["birth_latitude"] = geo_result["latitude"]
                self.user_data["birth_longitude"] = geo_result["longitude"]
                self.user_data["birth_timezone"] = geo_result["timezone"]
                print_success(f"Found: {geo_result['address']}")
                print_success(f"Coordinates: {geo_result['latitude']:.4f}, {geo_result['longitude']:.4f}")
                print_success(f"Timezone: {geo_result['timezone']}")
            else:
                raise Exception("Location not found")
        except Exception as e:
            print_warning(f"Geocoding failed: {e}")
            print_info("Using default coordinates for Los Angeles")
            self.user_data["birth_latitude"] = 34.0522
            self.user_data["birth_longitude"] = -118.2437
            self.user_data["birth_timezone"] = "America/Los_Angeles"
        
        print_success("\nBirth data collected!")
        return self.user_data
    
    def run_astrology_calculation(self) -> dict:
        """Run astrology calculation."""
        print_section("Astrology Calculation")
        
        try:
            from app.modules.calculation.astrology.brain.calculator import calculate_natal_chart
            from app.modules.calculation.astrology.brain.interpreter import format_chart_summary
            
            chart = calculate_natal_chart(
                name=self.user_data["name"],
                birth_date=self.user_data["birth_date"],
                birth_time=self.user_data.get("birth_time"),
                latitude=self.user_data["birth_latitude"],
                longitude=self.user_data["birth_longitude"],
                timezone=self.user_data["birth_timezone"],
            )
            
            # Extract key info
            planets = chart.get("planets", [])
            sun = next((p for p in planets if p.get("name") == "Sun"), None)
            moon = next((p for p in planets if p.get("name") == "Moon"), None)
            ascendant = chart.get("ascendant", {})
            
            print_success("Natal chart calculated!")
            if sun:
                print(f"  ☉ Sun: {sun.get('sign', '?')} (House {sun.get('house', '?')})")
            if moon:
                print(f"  ☽ Moon: {moon.get('sign', '?')} (House {moon.get('house', '?')})")
            if ascendant:
                print(f"  ↑ Rising: {ascendant.get('sign', '?')}")
            
            # Get summary
            summary = format_chart_summary(chart)
            print(f"\n  Summary: {summary}")
            
            self.profile_data["astrology"] = chart
            return chart
            
        except Exception as e:
            print_error(f"Astrology calculation failed: {e}")
            # Return mock data
            mock_chart = {
                "planets": [
                    {"name": "Sun", "sign": "Taurus", "house": 10, "degree": 24.5},
                    {"name": "Moon", "sign": "Scorpio", "house": 4, "degree": 15.3},
                ],
                "ascendant": {"sign": "Leo", "degree": 12.7},
                "aspects": [],
                "houses": []
            }
            self.profile_data["astrology"] = mock_chart
            print_warning("Using mock astrology data")
            return mock_chart
    
    def run_human_design_calculation(self) -> dict:
        """Run Human Design calculation."""
        print_section("Human Design Calculation")
        
        try:
            from app.modules.calculation.human_design.brain.calculator import calculate_human_design_chart
            
            chart = calculate_human_design_chart(
                name=self.user_data["name"],
                birth_date=self.user_data["birth_date"],
                birth_time=self.user_data.get("birth_time"),
                latitude=self.user_data["birth_latitude"],
                longitude=self.user_data["birth_longitude"],
                timezone=self.user_data["birth_timezone"],
            )
            
            print_success("Human Design chart calculated!")
            print(f"  Type: {chart.get('type', '?')}")
            print(f"  Strategy: {chart.get('strategy', '?')}")
            print(f"  Authority: {chart.get('authority', '?')}")
            print(f"  Profile: {chart.get('profile', '?')}")
            
            self.profile_data["human_design"] = chart
            return chart
            
        except Exception as e:
            print_error(f"Human Design calculation failed: {e}")
            # Return mock data
            mock_chart = {
                "type": "Projector",
                "strategy": "Wait for Invitation",
                "authority": "Emotional - Solar Plexus",
                "profile": "4/6",
                "defined_centers": ["Head", "Ajna", "Throat"],
                "open_centers": ["Solar Plexus", "Sacral", "Root", "Spleen", "Heart", "G Center"]
            }
            self.profile_data["human_design"] = mock_chart
            print_warning("Using mock Human Design data")
            return mock_chart
    
    def run_numerology_calculation(self) -> dict:
        """Run numerology calculation."""
        print_section("Numerology Calculation")
        
        try:
            from app.modules.calculation.numerology.brain.calculator import calculate_numerology_chart
            
            chart = calculate_numerology_chart(
                name=self.user_data["name"],
                birth_date=self.user_data["birth_date"],
            )
            
            print_success("Numerology chart calculated!")
            life_path = chart.get("life_path", {})
            expression = chart.get("expression", {})
            soul_urge = chart.get("soul_urge", {})
            
            print(f"  Life Path: {life_path.get('number', '?')}")
            print(f"  Expression: {expression.get('number', '?')}")
            print(f"  Soul Urge: {soul_urge.get('number', '?')}")
            
            self.profile_data["numerology"] = chart
            return chart
            
        except Exception as e:
            print_error(f"Numerology calculation failed: {e}")
            # Return mock data
            mock_chart = {
                "life_path": {"number": 7, "name": "The Seeker"},
                "expression": {"number": 3, "name": "The Creative"},
                "soul_urge": {"number": 5, "name": "The Freedom Seeker"}
            }
            self.profile_data["numerology"] = mock_chart
            print_warning("Using mock numerology data")
            return mock_chart
    
    async def generate_synthesis(self) -> str:
        """Generate unified synthesis."""
        print_section("Generating Unified Synthesis")
        
        if self.use_live_llm:
            try:
                from app.modules.intelligence.synthesis.synthesizer import ProfileSynthesizer
                from app.modules.intelligence.synthesis.schemas import ModuleInsights
                
                # Create synthesizer
                synthesizer = ProfileSynthesizer(model_id="anthropic/claude-3.5-sonnet")
                
                # Build insights manually since we're not using DB
                module_insights = {}
                for module_name, data in self.profile_data.items():
                    insights = synthesizer._extract_key_insights(module_name, data)
                    module_insights[module_name] = insights
                
                # Build prompt
                prompt = synthesizer._build_synthesis_prompt(module_insights)
                
                # Call LLM
                from langchain_core.messages import HumanMessage, SystemMessage
                
                print_info("Calling AI for synthesis (this may take a moment)...")
                
                response = await synthesizer.llm.ainvoke([
                    SystemMessage(content="You are a master synthesist who finds profound connections across wisdom traditions. Your insights are warm, practical, and deeply personal."),
                    HumanMessage(content=prompt)
                ])
                
                synthesis = response.content if isinstance(response.content, str) else str(response.content)
                print_success("Synthesis complete!")
                return synthesis
                
            except Exception as e:
                print_error(f"LLM synthesis failed: {e}")
                return self._generate_template_synthesis()
        else:
            return self._generate_template_synthesis()
    
    def _generate_template_synthesis(self) -> str:
        """Generate template-based synthesis."""
        astro = self.profile_data.get("astrology", {})
        hd = self.profile_data.get("human_design", {})
        num = self.profile_data.get("numerology", {})
        
        planets = astro.get("planets", [])
        sun = next((p for p in planets if p.get("name") == "Sun"), {})
        moon = next((p for p in planets if p.get("name") == "Moon"), {})
        asc = astro.get("ascendant", {})
        
        return f"""
Your Unified Cosmic Profile - {self.user_data['name']}

🌟 CORE ESSENCE
Your {sun.get('sign', 'Sun sign')} Sun illuminates your path with its unique energy, while 
your {moon.get('sign', 'Moon sign')} Moon governs your emotional world and inner needs. 
With {asc.get('sign', 'your rising sign')} Rising, the world first sees you as someone with 
that energy at the forefront.

⚡ HUMAN DESIGN STRATEGY
As a {hd.get('type', 'unique type')}, your strategy is to "{hd.get('strategy', 'follow your design')}". 
Your {hd.get('authority', 'inner authority')} authority guides your decisions. 
Your {hd.get('profile', 'profile')} profile shapes how you learn and share wisdom.

🔢 NUMEROLOGICAL PATH
Your Life Path {num.get('life_path', {}).get('number', '?')} suggests a journey of 
{num.get('life_path', {}).get('name', 'discovery')}. 
Combined with Expression Number {num.get('expression', {}).get('number', '?')}, 
you naturally channel creative and communicative energy.

🔮 SYNTHESIS
These systems paint a unified picture: You're designed to be seen and recognized 
for your unique gifts, but in a way that honors your own timing and inner truth. 
The key is patience - waiting for the right invitations while staying true to 
your emotional wisdom.
"""
    
    async def answer_question(self, question: str) -> str:
        """Answer a question about the profile."""
        if self.use_live_llm:
            try:
                from app.modules.intelligence.query.engine import QueryEngine
                import json
                
                engine = QueryEngine(model_id="anthropic/claude-3.5-sonnet")
                
                # Build context manually
                context = await engine._build_context_from_data(self.profile_data)
                
                print_info("Calling AI to answer your question...")
                
                answer, confidence = await engine._generate_answer(
                    question,
                    context,
                    list(self.profile_data.keys()),
                    "demo-trace"
                )
                
                return answer
                
            except AttributeError:
                # Fall back to direct LLM call
                try:
                    from app.core.ai.llm_factory import get_llm
                    from langchain_core.messages import HumanMessage, SystemMessage
                    
                    llm = get_llm("anthropic/claude-3.5-sonnet", temperature=0.7)
                    
                    # Build context
                    context = self._build_context()
                    
                    prompt = f"""Answer this question using the person's cosmic profile data.

QUESTION: {question}

PROFILE DATA:
{context}

Answer warmly and specifically, citing which systems provide each insight."""

                    response = await llm.ainvoke([
                        SystemMessage(content="You are a compassionate guide with deep knowledge of astrology, Human Design, and numerology."),
                        HumanMessage(content=prompt)
                    ])
                    
                    return response.content if isinstance(response.content, str) else str(response.content)
                    
                except Exception as e:
                    print_error(f"LLM query failed: {e}")
                    return self._generate_template_answer(question)
        else:
            return self._generate_template_answer(question)
    
    def _build_context(self) -> str:
        """Build context string from profile data."""
        parts = []
        
        astro = self.profile_data.get("astrology", {})
        if astro:
            parts.append("## Astrology")
            planets = astro.get("planets", [])
            for p in planets[:5]:
                parts.append(f"- {p.get('name', '?')}: {p.get('sign', '?')} (House {p.get('house', '?')})")
            asc = astro.get("ascendant", {})
            if asc:
                parts.append(f"- Ascendant: {asc.get('sign', '?')}")
        
        hd = self.profile_data.get("human_design", {})
        if hd:
            parts.append("\n## Human Design")
            parts.append(f"- Type: {hd.get('type', '?')}")
            parts.append(f"- Strategy: {hd.get('strategy', '?')}")
            parts.append(f"- Authority: {hd.get('authority', '?')}")
            parts.append(f"- Profile: {hd.get('profile', '?')}")
        
        num = self.profile_data.get("numerology", {})
        if num:
            parts.append("\n## Numerology")
            lp = num.get("life_path", {})
            parts.append(f"- Life Path: {lp.get('number', '?')}")
            exp = num.get("expression", {})
            parts.append(f"- Expression: {exp.get('number', '?')}")
        
        return "\n".join(parts)
    
    def _generate_template_answer(self, question: str) -> str:
        """Generate template-based answer."""
        q_lower = question.lower()
        
        hd = self.profile_data.get("human_design", {})
        astro = self.profile_data.get("astrology", {})
        
        if "authority" in q_lower or "decision" in q_lower:
            return f"Based on your Human Design, your {hd.get('authority', 'inner authority')} is key to making aligned decisions. As a {hd.get('type', 'unique type')}, remember your strategy: {hd.get('strategy', 'follow your design')}."
        
        elif "purpose" in q_lower or "life path" in q_lower:
            num = self.profile_data.get("numerology", {})
            lp = num.get("life_path", {})
            return f"Your Life Path {lp.get('number', '?')} suggests your purpose involves {lp.get('name', 'discovery and growth')}. Your Human Design type as a {hd.get('type', 'unique being')} shows you're here to {hd.get('strategy', 'live authentically')}."
        
        elif "relationship" in q_lower or "love" in q_lower:
            planets = astro.get("planets", [])
            moon = next((p for p in planets if p.get("name") == "Moon"), {})
            return f"In relationships, your {moon.get('sign', 'Moon sign')} Moon shapes your emotional needs. As a {hd.get('type', 'unique type')}, you connect best when you {hd.get('strategy', 'honor your design')}."
        
        else:
            return f"Based on your profile:\n{self._build_context()}\n\nThis gives you a unique perspective on '{question}'. Consider how your {hd.get('type', 'design')} and {hd.get('authority', 'authority')} can guide you here."
    
    async def run_interactive_chat(self):
        """Run interactive Q&A session."""
        print_header("Interactive Chat")
        
        print(f"{Colors.BOLD}Ask me anything about your cosmic profile!{Colors.ENDC}")
        print(f"{Colors.YELLOW}Type 'quit' or 'exit' to end the session.{Colors.ENDC}")
        print(f"{Colors.YELLOW}Type 'synthesis' to see your full profile synthesis.{Colors.ENDC}\n")
        
        while True:
            try:
                question = input(f"\n{Colors.GREEN}You:{Colors.ENDC} ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ["quit", "exit", "q"]:
                    print_info("Ending chat session. Goodbye!")
                    break
                
                if question.lower() == "synthesis":
                    synthesis = await self.generate_synthesis()
                    print_ai_response(synthesis)
                    continue
                
                if question.lower() == "profile":
                    print_ai_response(self._build_context())
                    continue
                
                answer = await self.answer_question(question)
                print_ai_response(answer)
                
            except KeyboardInterrupt:
                print_info("\nEnding chat session. Goodbye!")
                break
            except EOFError:
                print_info("\nEnding chat session. Goodbye!")
                break


async def main():
    """Main entry point."""
    print_header("GUTTERS Interactive Demo")
    print("""
Welcome to the GUTTERS (Grand Unified Theory of Transpersonal Energetic 
Resonance Synthesis) Interactive Demo!

This demo will:
1. Collect your birth data
2. Run calculations for Astrology, Human Design, and Numerology
3. Generate a unified synthesis of your cosmic profile
4. Allow you to chat and ask questions

Let's begin!
""")
    
    demo = GuttersDemo()
    
    # Check for API key
    demo.check_api_key()
    
    # Collect birth data
    demo.collect_birth_data()
    
    # Run calculations
    print_header("Running Calculations")
    demo.run_astrology_calculation()
    demo.run_human_design_calculation()
    demo.run_numerology_calculation()
    
    # Generate synthesis
    print_header("Unified Synthesis")
    synthesis = await demo.generate_synthesis()
    print(synthesis)
    
    # Interactive chat
    await demo.run_interactive_chat()
    
    print_header("Session Complete")
    print("Thank you for using the GUTTERS demo!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
