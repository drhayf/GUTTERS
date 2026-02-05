"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ORACLE DATABASE MODELS                                ║
║                                                                              ║
║   Persistent storage for Oracle readings with quest/journal integration.    ║
║                                                                              ║
║   Author: GUTTERS Project                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.app.core.db.database import Base


class OracleReading(Base):
    """
    Represents a single Oracle draw (Card + Hexagram + LLM synthesis).
    
    Links to the Intelligence Ecosystem:
    - Can spawn a Quest (when user accepts the mission)
    - Can spawn a ReflectionPrompt (the diagnostic question)
    """
    __tablename__ = "oracle_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)

    # The Draw
    card_rank: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-13
    card_suit: Mapped[str] = mapped_column(String, nullable=False)  # Hearts, Clubs, Diamonds, Spades
    hexagram_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-64
    hexagram_line: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-6

    # The Synthesis
    synthesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostic_question: Mapped[str] = mapped_column(Text, nullable=False)

    # Context snapshot at time of draw
    transit_context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # User interaction
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    reflected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Links to spawned entities
    quest_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quests.id"), nullable=True)
    prompt_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reflection_prompts.id"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    # Relationships
    user = relationship("User", backref="oracle_readings", lazy="select")
    quest = relationship("Quest", foreign_keys=[quest_id], lazy="select")
    prompt = relationship("ReflectionPrompt", foreign_keys=[prompt_id], lazy="select")
