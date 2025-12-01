"""
Journaling Tracker - Entry CRUD and History

This sub-module handles all entry tracking operations:
- Entry creation, update, delete
- History retrieval and search
- Entry statistics

@module JournalingTracker
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import date, datetime
import logging

from ..schema import JournalEntry, EntryType, MoodLevel

logger = logging.getLogger(__name__)


# =============================================================================
# ENTRY TRACKER
# =============================================================================

@dataclass
class EntryStats:
    """Statistics about journal entries."""
    total_entries: int = 0
    total_words: int = 0
    average_word_count: float = 0.0
    entries_by_type: Dict[str, int] = None
    entries_by_mood: Dict[str, int] = None
    
    def __post_init__(self):
        if self.entries_by_type is None:
            self.entries_by_type = {}
        if self.entries_by_mood is None:
            self.entries_by_mood = {}


class EntryTracker:
    """
    Tracks and manages journal entries.
    
    SCAFFOLD: Basic in-memory implementation.
    Full implementation will use persistent storage.
    """
    
    def __init__(self):
        self._entries: Dict[str, JournalEntry] = {}
    
    async def create(self, entry: JournalEntry) -> JournalEntry:
        """Create a new entry."""
        self._entries[entry.entry_id] = entry
        logger.info(f"Created entry: {entry.entry_id}")
        return entry
    
    async def get(self, entry_id: str) -> Optional[JournalEntry]:
        """Get an entry by ID."""
        return self._entries.get(entry_id)
    
    async def update(self, entry: JournalEntry) -> JournalEntry:
        """Update an existing entry."""
        entry.updated_at = datetime.now()
        self._entries[entry.entry_id] = entry
        return entry
    
    async def delete(self, entry_id: str) -> bool:
        """Delete an entry."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False
    
    async def list_all(self, limit: int = 100) -> List[JournalEntry]:
        """List all entries."""
        entries = list(self._entries.values())
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]


class EntryHistory:
    """
    Provides historical analysis of entries.
    
    SCAFFOLD: Basic implementation.
    """
    
    def __init__(self, tracker: EntryTracker):
        self._tracker = tracker
    
    async def get_entries_for_period(
        self,
        start_date: date,
        end_date: date,
    ) -> List[JournalEntry]:
        """Get entries within a date range."""
        all_entries = await self._tracker.list_all(limit=1000)
        return [
            e for e in all_entries
            if start_date <= e.created_at.date() <= end_date
        ]
    
    async def get_stats(self, days: int = 30) -> EntryStats:
        """Get entry statistics for the past N days."""
        entries = await self._tracker.list_all(limit=1000)
        
        if not entries:
            return EntryStats()
        
        total_words = sum(e.word_count for e in entries)
        
        return EntryStats(
            total_entries=len(entries),
            total_words=total_words,
            average_word_count=total_words / len(entries) if entries else 0,
        )


class EntrySearch:
    """
    Search functionality for entries.
    
    SCAFFOLD: Basic text search.
    Full implementation will use vector search.
    """
    
    def __init__(self, tracker: EntryTracker):
        self._tracker = tracker
    
    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> List[JournalEntry]:
        """Search entries by content."""
        all_entries = await self._tracker.list_all(limit=1000)
        query_lower = query.lower()
        
        matches = [
            e for e in all_entries
            if query_lower in e.content.lower()
        ]
        
        return matches[:limit]
    
    async def find_by_tags(self, tags: List[str]) -> List[JournalEntry]:
        """Find entries with specific tags."""
        all_entries = await self._tracker.list_all(limit=1000)
        
        return [
            e for e in all_entries
            if any(tag in e.tags for tag in tags)
        ]


__all__ = [
    "EntryTracker",
    "EntryHistory",
    "EntrySearch",
    "EntryStats",
]
