"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ORACLE SERVICE - DIVINATION ENGINE                    ║
║                                                                              ║
║   Cryptographically secure random oracle readings with LLM synthesis.       ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import structlog
import secrets
from datetime import datetime, timezone, date
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.llm.config import LLMConfig
from src.app.modules.intelligence.synthesis import get_user_preferred_model, ALLOWED_MODELS
from src.app.modules.intelligence.cardology import CardologyModule
from src.app.modules.intelligence.cardology.kernel import Card, Suit
from src.app.modules.intelligence.iching import IChingKernel, GATE_DATABASE
from src.app.modules.intelligence.synthesis.harmonic import (
    CouncilOfSystems,
    IChingAdapter,
    CardologyAdapter,
)
from src.app.modules.features.quests.models import Quest, QuestCategory, QuestSource, QuestDifficulty
from src.app.models.insight import ReflectionPrompt, PromptPhase, PromptStatus
from .models import OracleReading

logger = structlog.get_logger(__name__)


class OracleService:
    """
    The System Oracle - Divination through cryptographically secure randomness.
    
    Architecture:
    1. Crypto-secure random selection (Card + Hexagram)
    2. Council of Systems synthesis
    3. LLM diagnostic question generation
    4. Quest/Journal integration
    """
    
    def __init__(self):
        """Initialize Oracle Service."""
        self.cardology_module = CardologyModule()
        self.iching_kernel = IChingKernel()
        # LLM will be fetched per-user based on their preferences
        
    async def _get_user_llm(self, user_id: int, db: AsyncSession):
        """Get LLM instance based on user's preferred model."""
        from langchain_openai import ChatOpenAI
        from src.app.core.config import settings
        
        # Fetch user's preferred model
        preferred_model = await get_user_preferred_model(user_id, db)
        
        # Create LLM with user's preferred model
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            model=preferred_model,
            temperature=0.7,
            max_tokens=4000,
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": "https://gutters.app",
                    "X-Title": "GUTTERS - Oracle Reading",
                }
            },
        )
    
    async def perform_daily_draw(
        self,
        user_id: int,
        db: AsyncSession,
        birth_date: Optional[date] = None
    ) -> OracleReading:
        """
        Perform a complete Oracle reading for a user.
        
        Steps:
        1. Crypto-secure random selection of Card (1-52) and Hexagram (1-64)
        2. Fetch current transit context
        3. Cross-system synthesis via CouncilOfSystems
        4. LLM diagnostic question generation
        5. Persist to database
        
        Args:
            user_id: User ID for reading
            db: Database session
            birth_date: User's birth date for personalized context
            
        Returns:
            OracleReading with full synthesis
        """
        logger.info("oracle.draw.start", user_id=user_id)
        
        # STEP 1: Crypto-secure random selection
        card_rank, card_suit = self._random_card()
        hexagram_number, hexagram_line = self._random_hexagram()
        
        logger.info(
            "oracle.draw.selected",
            user_id=user_id,
            card=f"{card_rank} of {card_suit}",
            hexagram=hexagram_number,
            line=hexagram_line
        )
        
        # STEP 2: Get transit context
        now = datetime.now(timezone.utc)
        transit_context = await self._gather_transit_context(user_id, birth_date, now)
        
        # STEP 3: Generate synthesis
        synthesis_text = await self._generate_synthesis(
            card_rank=card_rank,
            card_suit=card_suit,
            hexagram_number=hexagram_number,
            hexagram_line=hexagram_line,
            transit_context=transit_context,
            birth_date=birth_date,
            user_id=user_id,
            db=db
        )
        
        # STEP 4: Generate diagnostic question
        diagnostic_question = await self._generate_diagnostic_question(
            card_rank=card_rank,
            card_suit=card_suit,
            hexagram_number=hexagram_number,
            synthesis_text=synthesis_text,
            transit_context=transit_context,
            user_id=user_id,
            db=db
        )
        
        # STEP 5: Persist reading
        reading = OracleReading(
            user_id=user_id,
            card_rank=card_rank,
            card_suit=card_suit,
            hexagram_number=hexagram_number,
            hexagram_line=hexagram_line,
            synthesis_text=synthesis_text,
            diagnostic_question=diagnostic_question,
            transit_context=transit_context,
            accepted=False,
            reflected=False
        )
        
        db.add(reading)
        await db.commit()
        await db.refresh(reading)
        
        logger.info("oracle.draw.complete", user_id=user_id, reading_id=reading.id)
        
        return reading
    
    def _random_card(self) -> Tuple[int, str]:
        """
        Select a random card using cryptographically secure entropy.
        
        Uses secrets.SystemRandom which is backed by os.urandom
        (cryptographically secure PRNG).
        
        Returns:
            Tuple of (rank: 1-13, suit: str)
        """
        rank = secrets.randbelow(13) + 1  # 1-13 (Ace to King)
        suits = ["Hearts", "Clubs", "Diamonds", "Spades"]
        suit = suits[secrets.randbelow(4)]
        
        return rank, suit
    
    def _random_hexagram(self) -> Tuple[int, int]:
        """
        Select a random hexagram and line using cryptographically secure entropy.
        
        Returns:
            Tuple of (hexagram: 1-64, line: 1-6)
        """
        hexagram = secrets.randbelow(64) + 1  # 1-64
        line = secrets.randbelow(6) + 1  # 1-6
        
        return hexagram, line
    
    async def _gather_transit_context(
        self,
        user_id: int,
        birth_date: Optional[date],
        dt: datetime
    ) -> Dict[str, Any]:
        """
        Gather current transit state for context.
        
        Returns:
            Dict with current planetary period, hexagram, and other transits
        """
        context = {
            "timestamp": dt.isoformat(),
            "user_id": user_id
        }
        
        # Get current I-Ching transit
        daily_code = self.iching_kernel.get_daily_code(dt)
        sun = daily_code.sun_activation
        earth = daily_code.earth_activation
        
        context["current_sun_gate"] = sun.gate
        context["current_sun_line"] = sun.line
        context["current_earth_gate"] = earth.gate
        
        # Get current Cardology period
        if birth_date:
            try:
                period_info = self.cardology_module.get_current_period(birth_date, dt.date())
                if period_info:
                    context["current_period_card"] = str(period_info.get("period_card", {}).get("name", "Unknown"))
                    context["current_planetary_ruler"] = period_info.get("planetary_ruler", "Unknown")
            except Exception as e:
                logger.warning("oracle.context.cardology_error", error=str(e))
        
        return context
    
    async def _generate_synthesis(
        self,
        card_rank: int,
        card_suit: str,
        hexagram_number: int,
        hexagram_line: int,
        transit_context: Dict[str, Any],
        birth_date: Optional[date],
        user_id: int,
        db: AsyncSession
    ) -> str:
        """
        Generate cross-system synthesis using CouncilOfSystems.
        
        This leverages the existing harmonic synthesis architecture
        to create a coherent story between Card and Hexagram.
        """
        # Get detailed data for each symbol
        card_data = self._get_card_data(card_rank, card_suit)
        hexagram_data = self._get_hexagram_data(hexagram_number, hexagram_line)
        
        # Build synthesis prompt for LLM
        synthesis_prompt = self._build_synthesis_prompt(
            card_data=card_data,
            hexagram_data=hexagram_data,
            transit_context=transit_context
        )
        
        # Use Council Service to generate synthesis
        try:
            llm = await self._get_user_llm(user_id, db)
            response = await llm.ainvoke(synthesis_prompt)
            synthesis = response.content
            return synthesis
        except Exception as e:
            logger.error("oracle.synthesis.error", error=str(e))
            # Fallback to basic synthesis
            return self._fallback_synthesis(card_data, hexagram_data)
    
    def _get_card_data(self, rank: int, suit: str) -> Dict[str, Any]:
        """Extract comprehensive card data."""
        suit_enum = getattr(Suit, suit.upper())
        card = Card(rank=rank, suit=suit_enum)
        
        rank_names = {1: "Ace", 11: "Jack", 12: "Queen", 13: "King"}
        rank_name = rank_names.get(rank, str(rank))
        
        # Cardology meanings (simplified - can expand)
        suit_meanings = {
            "Hearts": {
                "element": "Water",
                "domain": "Emotions, Love, Relationships",
                "keynote": "Heart-centered connection"
            },
            "Clubs": {
                "element": "Fire",
                "domain": "Knowledge, Ideas, Communication",
                "keynote": "Mental fire and learning"
            },
            "Diamonds": {
                "element": "Earth",
                "domain": "Values, Money, Material world",
                "keynote": "Manifestation and worth"
            },
            "Spades": {
                "element": "Air",
                "domain": "Work, Health, Transformation",
                "keynote": "Spiritual work and mastery"
            }
        }
        
        return {
            "rank": rank,
            "rank_name": rank_name,
            "suit": suit,
            "full_name": f"{rank_name} of {suit}",
            "symbol": str(card),
            "meanings": suit_meanings.get(suit, {}),
            "solar_value": card.solar_value
        }
    
    def _get_hexagram_data(self, hexagram_number: int, line: int) -> Dict[str, Any]:
        """Extract comprehensive hexagram data."""
        gate_data = GATE_DATABASE.get(hexagram_number)
        
        if not gate_data:
            return {
                "number": hexagram_number,
                "line": line,
                "name": f"Gate {hexagram_number}",
                "keynote": "Unknown",
                "shadow": "Unknown",
                "gift": "Unknown",
                "siddhi": "Unknown"
            }
        
        # Get line-specific data if available
        line_data = gate_data.lines.get(line, None) if gate_data.lines else None
        
        return {
            "number": hexagram_number,
            "line": line,
            "iching_name": gate_data.iching_name,
            "hd_name": gate_data.hd_name,
            "keynote": gate_data.hd_keynote,
            "shadow": gate_data.gk_shadow,
            "gift": gate_data.gk_gift,
            "siddhi": gate_data.gk_siddhi,
            "line_name": line_data.name if line_data else f"Line {line}",
            "line_keynote": line_data.keynote if line_data else "",
            "line_archetype": self._get_line_archetype(line)
        }
    
    def _get_line_archetype(self, line: int) -> str:
        """Get the archetypal meaning of each line (1-6)."""
        archetypes = {
            1: "The Foundation (Investigator)",
            2: "The Inner Stability (Hermit)",
            3: "The Trial by Fire (Martyr)",
            4: "The Network (Opportunist)",
            5: "The Universal (Heretic)",
            6: "The Role Model (Administrator)"
        }
        return archetypes.get(line, f"Line {line}")
    
    def _build_synthesis_prompt(
        self,
        card_data: Dict[str, Any],
        hexagram_data: Dict[str, Any],
        transit_context: Dict[str, Any]
    ) -> str:
        """Build LLM prompt for Oracle synthesis."""
        return f"""You are the System Oracle, synthesizing wisdom from Cardology and I-Ching.

**The Draw:**
- **Card**: {card_data['full_name']}
  - Element: {card_data['meanings'].get('element', 'Unknown')}
  - Domain: {card_data['meanings'].get('domain', 'Unknown')}
  - Keynote: {card_data['meanings'].get('keynote', 'Unknown')}

- **Hexagram**: Gate {hexagram_data['number']} - {hexagram_data['hd_name']}
  - Line {hexagram_data['line']}: {hexagram_data['line_archetype']}
  - Shadow: {hexagram_data['shadow']}
  - Gift: {hexagram_data['gift']}
  - Siddhi: {hexagram_data['siddhi']}

**Current Transits:**
- Sun Gate: {transit_context.get('current_sun_gate', 'Unknown')}
- Current Period Card: {transit_context.get('current_period_card', 'Unknown')}

**Task:**
Write a 3-4 paragraph Oracle reading that:
1. Reveals the **symbolic resonance** between the Card and Hexagram
2. Weaves their meanings into a coherent narrative
3. Provides **practical guidance** for embodying this wisdom
4. Speaks directly to the querent with clarity and depth

Be poetic yet precise. Avoid generic platitudes. This is a sacred reading."""
    
    def _fallback_synthesis(
        self,
        card_data: Dict[str, Any],
        hexagram_data: Dict[str, Any]
    ) -> str:
        """Fallback synthesis when LLM unavailable."""
        return f"""**{card_data['full_name']} × Gate {hexagram_data['number']}**

The {card_data['suit']} suit speaks to {card_data['meanings'].get('domain', 'life themes')}, while Gate {hexagram_data['number']} ({hexagram_data['hd_name']}) illuminates the path of {hexagram_data['keynote']}.

This reading invites you to integrate {card_data['meanings'].get('keynote', 'the card\'s wisdom')} with the energy of {hexagram_data['gift']}. Watch for the shadow of {hexagram_data['shadow']}, and cultivate the gift of {hexagram_data['gift']}.

Line {hexagram_data['line']} ({hexagram_data['line_archetype']}) is your focal point today. This line represents {hexagram_data.get('line_keynote', 'a particular quality of being')}."""
    
    async def _generate_diagnostic_question(
        self,
        card_rank: int,
        card_suit: str,
        hexagram_number: int,
        synthesis_text: str,
        transit_context: Dict[str, Any],
        user_id: int,
        db: AsyncSession
    ) -> str:
        """
        Generate a probing diagnostic question using LLM.
        
        This question aims to reveal unconscious patterns or suppressed desires.
        """
        card_data = self._get_card_data(card_rank, card_suit)
        hexagram_data = self._get_hexagram_data(hexagram_number, 1)  # Line doesn't matter here
        
        prompt = f"""You are a depth psychologist and oracle interpreter.

**The User Drew:**
- {card_data['full_name']}
- Gate {hexagram_number}: {hexagram_data['hd_name']}

**Their Recent Context:**
- Current transit: Gate {transit_context.get('current_sun_gate', 'Unknown')}
- Period: {transit_context.get('current_period_card', 'Unknown')}

**Oracle Synthesis:**
{synthesis_text[:500]}...

**Task:**
Generate ONE piercing diagnostic question that:
1. Points to a potential blind spot or suppressed truth
2. Creates healthy discomfort (not brutal, but sharp)
3. Invites genuine self-inquiry
4. Is specific to THIS draw (not generic)

Format: Just the question, no preamble. 1-2 sentences max.

Example style: "The {card_data['suit']} speaks of {card_data['meanings']['domain'].lower()}, yet your logs show {{}}- are you performing connection while avoiding real intimacy?"
"""
        
        try:
            llm = await self._get_user_llm(user_id, db)
            response = await llm.ainvoke(prompt)
            question = response.content
            return question.strip()
        except Exception as e:
            logger.error("oracle.diagnostic.error", error=str(e))
            # Fallback question
            return f"The {card_data['full_name']} and Gate {hexagram_number} both emphasize {hexagram_data['keynote']} - where in your life are you avoiding this theme?"
    
    async def accept_reading(
        self,
        reading_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Quest:
        """
        User accepts the Oracle reading - create a Quest.
        
        Quest Spec:
        - Category: MISSION
        - Source: ORACLE
        - Title: "Embodying the [Card Name]"
        - XP: Based on difficulty + insight bonus
        
        Args:
            reading_id: Oracle reading ID
            user_id: User ID
            db: Database session
            
        Returns:
            Created Quest
        """
        # Fetch reading
        result = await db.execute(
            select(OracleReading).where(
                OracleReading.id == reading_id,
                OracleReading.user_id == user_id
            )
        )
        reading = result.scalar_one_or_none()
        
        if not reading:
            raise ValueError(f"Reading {reading_id} not found for user {user_id}")
        
        if reading.accepted:
            raise ValueError(f"Reading {reading_id} already accepted")
        
        # Build quest from reading
        card_data = self._get_card_data(reading.card_rank, reading.card_suit)
        hexagram_data = self._get_hexagram_data(reading.hexagram_number, reading.hexagram_line)
        
        quest_title = f"Embodying the {card_data['full_name']}"
        quest_description = f"""**Oracle Mission**

You have drawn the {card_data['full_name']} paired with Gate {hexagram_data['number']} ({hexagram_data['hd_name']}).

**Your Task:**
Consciously embody the wisdom of this reading throughout your day. Practice moving from the shadow of {hexagram_data['shadow']} into the gift of {hexagram_data['gift']}.

**Synthesis:**
{reading.synthesis_text[:300]}...

**Reflection:**
{reading.diagnostic_question}"""
        
        # Determine XP reward (base + insight bonus)
        base_xp = 250  # MISSION category base
        insight_bonus = 100  # Oracle readings grant bonus XP
        total_xp = base_xp + insight_bonus
        
        # Create Quest
        quest = Quest(
            user_id=user_id,
            title=quest_title,
            description=quest_description,
            category=QuestCategory.MISSION,
            source=QuestSource.AGENT,  # Oracle is an agent source
            difficulty=QuestDifficulty.MEDIUM,
            xp_reward=total_xp,
            insight_id=None,  # Not linked to reflection prompt
            tags=f"oracle,{card_data['suit'].lower()},gate{hexagram_data['number']}"
        )
        
        db.add(quest)
        
        # Update reading
        reading.accepted = True
        reading.quest_id = quest.id
        
        await db.commit()
        await db.refresh(quest)
        
        logger.info(
            "oracle.quest.created",
            user_id=user_id,
            reading_id=reading_id,
            quest_id=quest.id,
            xp=total_xp
        )
        
        return quest
    
    async def reflect_on_reading(
        self,
        reading_id: int,
        user_id: int,
        db: AsyncSession
    ) -> ReflectionPrompt:
        """
        User chooses to reflect on reading - create a ReflectionPrompt.
        
        Args:
            reading_id: Oracle reading ID
            user_id: User ID
            db: Database session
            
        Returns:
            Created ReflectionPrompt
        """
        # Fetch reading
        result = await db.execute(
            select(OracleReading).where(
                OracleReading.id == reading_id,
                OracleReading.user_id == user_id
            )
        )
        reading = result.scalar_one_or_none()
        
        if not reading:
            raise ValueError(f"Reading {reading_id} not found for user {user_id}")
        
        if reading.reflected:
            raise ValueError(f"Reading {reading_id} already has reflection prompt")
        
        # Create ReflectionPrompt with diagnostic question
        prompt = ReflectionPrompt(
            user_id=user_id,
            prompt_text=reading.diagnostic_question,
            topic="oracle_reading",
            trigger_context={
                "reading_id": reading_id,
                "card": f"{reading.card_rank} of {reading.card_suit}",
                "hexagram": reading.hexagram_number,
                "line": reading.hexagram_line
            },
            event_phase=PromptPhase.PEAK,  # Oracle readings are peak moments
            status=PromptStatus.PENDING
        )
        
        db.add(prompt)
        
        # Update reading
        reading.reflected = True
        reading.prompt_id = prompt.id
        
        await db.commit()
        await db.refresh(prompt)
        
        logger.info(
            "oracle.prompt.created",
            user_id=user_id,
            reading_id=reading_id,
            prompt_id=prompt.id
        )
        
        return prompt
    
    async def get_reading(
        self,
        reading_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[OracleReading]:
        """Fetch a specific Oracle reading."""
        result = await db.execute(
            select(OracleReading).where(
                OracleReading.id == reading_id,
                OracleReading.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_readings(
        self,
        user_id: int,
        db: AsyncSession,
        limit: int = 10
    ) -> list[OracleReading]:
        """Fetch user's recent Oracle readings."""
        result = await db.execute(
            select(OracleReading)
            .where(OracleReading.user_id == user_id)
            .order_by(OracleReading.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
