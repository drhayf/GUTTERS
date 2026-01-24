"""
Embedding model for vector search.

Stores semantic embeddings of all user content with JSONB metadata.
"""

from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, Text, ForeignKey, Index, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from src.app.core.db.database import Base

if TYPE_CHECKING:
    from .user import User


class Embedding(Base):
    """
    Vector embeddings for semantic search.

    Each row represents one piece of content (journal entry, synthesis, etc.)
    with its embedding and rich metadata for filtering.
    """

    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Original text
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))  # OpenAI text-embedding-3-small

    # Metadata (JSONB for flexible queries)
    content_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="embeddings", lazy="select")

    # Indexes (already defined in migration, but standardizing here)
    __table_args__ = (
        Index("ix_embeddings_user_id", "user_id"),
        Index("ix_embeddings_content_metadata", "content_metadata", postgresql_using="gin"),
    )
