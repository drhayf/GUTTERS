"""
Profile Storage - Persistent Storage for Digital Twin Profiles

This module handles saving, loading, and managing Genesis profiles:
- Save completed profiles with metadata
- Resume in-progress sessions
- Multiple profile slots (save games)
- Export/import for sharing

File Structure:
    data/
    ├── profiles/           # Completed profiles
    │   ├── profile_1.json
    │   ├── profile_2.json
    │   └── ...
    ├── sessions/           # In-progress sessions
    │   ├── {session_id}.json
    │   └── ...
    └── exports/            # Shareable exports
        └── {name}_{timestamp}.json

Usage:
    storage = get_profile_storage()
    
    # Save a completed profile
    slot_id = storage.save_profile(
        session_state=state,
        name="My First Profile",
    )
    
    # List saved profiles
    profiles = storage.list_profiles()
    
    # Load a profile
    profile = storage.load_profile(slot_id)
    
    # Resume an in-progress session
    state = storage.load_session(session_id)
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ProfileStatus(str, Enum):
    """Status of a saved profile."""
    IN_PROGRESS = "in_progress"     # Still being built
    COMPLETED = "completed"         # Fully completed profile
    ARCHIVED = "archived"           # Old version, kept for reference


@dataclass
class ProfileSlot:
    """
    A slot for storing a profile.
    
    Attributes:
        slot_id: Unique identifier for this slot (1-10 for user slots)
        name: User-defined name for the profile
        status: Whether the profile is complete
        created_at: When the profile was first created
        updated_at: Last modification time
        phase: Current/final phase of the profile
        completion_percentage: How complete the profile is
        total_responses: Number of interactions recorded
        summary: Brief summary of the profile
    """
    slot_id: str
    name: str
    status: ProfileStatus
    created_at: str
    updated_at: str
    phase: str
    completion_percentage: float
    total_responses: int
    summary: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "slot_id": self.slot_id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "phase": self.phase,
            "completion_percentage": self.completion_percentage,
            "total_responses": self.total_responses,
            "summary": self.summary,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProfileSlot":
        """Create from dictionary."""
        return cls(
            slot_id=data["slot_id"],
            name=data["name"],
            status=ProfileStatus(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            phase=data["phase"],
            completion_percentage=data["completion_percentage"],
            total_responses=data["total_responses"],
            summary=data.get("summary"),
        )


@dataclass
class SavedProfile:
    """
    A complete saved profile including all state data.
    
    This is the full data blob saved to disk, including:
    - Slot metadata
    - Complete session state (rubric, responses, etc.)
    - Digital Twin export (if completed)
    """
    slot: ProfileSlot
    session_state: dict              # Full GenesisState serialized
    digital_twin: Optional[dict]     # Exported Digital Twin (if complete)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "slot": self.slot.to_dict(),
            "session_state": self.session_state,
            "digital_twin": self.digital_twin,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SavedProfile":
        """Create from dictionary."""
        return cls(
            slot=ProfileSlot.from_dict(data["slot"]),
            session_state=data["session_state"],
            digital_twin=data.get("digital_twin"),
        )


# =============================================================================
# STORAGE ENGINE
# =============================================================================

class ProfileStorage:
    """
    Manages persistent storage for Genesis profiles.
    
    This class handles:
    - File I/O for profiles and sessions
    - Profile slot management
    - Session recovery
    - Export/import functionality
    
    Attributes:
        data_dir: Root directory for all data storage
        profiles_dir: Directory for saved profiles
        sessions_dir: Directory for in-progress sessions
        exports_dir: Directory for exports
    """
    
    MAX_SLOTS = 10  # Maximum number of saved profile slots
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the storage engine.
        
        Args:
            data_dir: Root directory for data. Defaults to ./data
        """
        if data_dir is None:
            # Default to ./data relative to the api directory
            api_dir = Path(__file__).parent.parent.parent
            data_dir = api_dir / "data"
        else:
            data_dir = Path(data_dir)
        
        self.data_dir = data_dir
        self.profiles_dir = data_dir / "profiles"
        self.sessions_dir = data_dir / "sessions"
        self.exports_dir = data_dir / "exports"
        
        # Ensure directories exist
        self._ensure_directories()
        
        logger.info(f"[ProfileStorage] Initialized with data_dir: {self.data_dir}")
    
    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        for directory in [self.data_dir, self.profiles_dir, self.sessions_dir, self.exports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # PROFILE MANAGEMENT
    # =========================================================================
    
    def save_profile(
        self,
        session_state: dict,
        name: str,
        digital_twin: Optional[dict] = None,
        slot_id: Optional[str] = None,
    ) -> str:
        """
        Save a profile to a slot.
        
        Args:
            session_state: The serialized GenesisState
            name: User-defined name for the profile
            digital_twin: The exported Digital Twin (if complete)
            slot_id: Specific slot to save to (or auto-assign)
        
        Returns:
            The slot_id where the profile was saved
        """
        now = datetime.utcnow().isoformat()
        
        # Determine slot ID
        if slot_id is None:
            slot_id = self._find_next_slot()
        
        # Determine status
        status = (
            ProfileStatus.COMPLETED 
            if session_state.get("profile_complete", False) 
            else ProfileStatus.IN_PROGRESS
        )
        
        # Create slot metadata
        slot = ProfileSlot(
            slot_id=slot_id,
            name=name,
            status=status,
            created_at=now,
            updated_at=now,
            phase=session_state.get("phase", "unknown"),
            completion_percentage=session_state.get("completion_percentage", 0.0),
            total_responses=len(session_state.get("responses", [])),
            summary=self._generate_summary(session_state, digital_twin),
        )
        
        # Create full profile
        profile = SavedProfile(
            slot=slot,
            session_state=session_state,
            digital_twin=digital_twin,
        )
        
        # Save to file
        filepath = self.profiles_dir / f"{slot_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"[ProfileStorage] Saved profile '{name}' to slot {slot_id}")
        return slot_id
    
    def load_profile(self, slot_id: str) -> Optional[SavedProfile]:
        """
        Load a profile from a slot.
        
        Args:
            slot_id: The slot to load from
        
        Returns:
            The loaded profile, or None if not found
        """
        filepath = self.profiles_dir / f"{slot_id}.json"
        
        if not filepath.exists():
            logger.warning(f"[ProfileStorage] Profile not found: {slot_id}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SavedProfile.from_dict(data)
        except Exception as e:
            logger.error(f"[ProfileStorage] Error loading profile {slot_id}: {e}")
            return None
    
    def list_profiles(self) -> List[ProfileSlot]:
        """
        List all saved profile slots.
        
        Returns:
            List of slot metadata (not full profile data)
        """
        slots = []
        
        for filepath in self.profiles_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                slot = ProfileSlot.from_dict(data["slot"])
                slots.append(slot)
            except Exception as e:
                logger.warning(f"[ProfileStorage] Error reading {filepath}: {e}")
        
        # Sort by updated_at, most recent first
        slots.sort(key=lambda s: s.updated_at, reverse=True)
        return slots
    
    def delete_profile(self, slot_id: str) -> bool:
        """
        Delete a profile from a slot.
        
        Args:
            slot_id: The slot to delete
        
        Returns:
            True if deleted, False if not found
        """
        filepath = self.profiles_dir / f"{slot_id}.json"
        
        if not filepath.exists():
            return False
        
        try:
            filepath.unlink()
            logger.info(f"[ProfileStorage] Deleted profile: {slot_id}")
            return True
        except Exception as e:
            logger.error(f"[ProfileStorage] Error deleting profile {slot_id}: {e}")
            return False
    
    def _find_next_slot(self) -> str:
        """Find the next available slot ID."""
        existing = set()
        
        for filepath in self.profiles_dir.glob("*.json"):
            existing.add(filepath.stem)
        
        # Find first available slot
        for i in range(1, self.MAX_SLOTS + 1):
            slot_id = f"slot_{i}"
            if slot_id not in existing:
                return slot_id
        
        # All slots full - overwrite oldest
        slots = self.list_profiles()
        if slots:
            oldest = min(slots, key=lambda s: s.updated_at)
            return oldest.slot_id
        
        return "slot_1"
    
    def _generate_summary(
        self, 
        session_state: dict, 
        digital_twin: Optional[dict]
    ) -> str:
        """Generate a brief summary of the profile."""
        parts = []
        
        # Phase info
        phase = session_state.get("phase", "unknown")
        completion = session_state.get("completion_percentage", 0)
        parts.append(f"{phase.title()} ({completion:.0f}% complete)")
        
        # Key traits from rubric if available
        rubric = session_state.get("rubric", {})
        hd = rubric.get("human_design", {})
        
        if hd.get("type", {}).get("value"):
            parts.append(f"HD: {hd['type']['value']}")
        
        # Digital Twin summary
        if digital_twin:
            energetic = digital_twin.get("energetic_signature", {})
            if energetic.get("hd_type"):
                parts.append(f"Type: {energetic['hd_type']}")
            if energetic.get("energy_pattern"):
                parts.append(f"Energy: {energetic['energy_pattern']}")
        
        return " | ".join(parts) if parts else "Profile in progress"
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def save_session(self, session_id: str, session_state: dict) -> None:
        """
        Save an in-progress session for later resumption.
        
        This is called periodically during profiling to enable crash recovery.
        
        Args:
            session_id: The unique session identifier
            session_state: The serialized GenesisState
        """
        filepath = self.sessions_dir / f"{session_id}.json"
        
        session_data = {
            "session_id": session_id,
            "saved_at": datetime.utcnow().isoformat(),
            "session_state": session_state,
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"[ProfileStorage] Saved session: {session_id}")
    
    def load_session(self, session_id: str) -> Optional[dict]:
        """
        Load an in-progress session.
        
        Args:
            session_id: The session to load
        
        Returns:
            The session_state dict, or None if not found
        """
        filepath = self.sessions_dir / f"{session_id}.json"
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("session_state")
        except Exception as e:
            logger.warning(f"[ProfileStorage] Error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a saved session.
        
        Args:
            session_id: The session to delete
        
        Returns:
            True if deleted, False if not found
        """
        filepath = self.sessions_dir / f"{session_id}.json"
        
        if not filepath.exists():
            return False
        
        try:
            filepath.unlink()
            logger.debug(f"[ProfileStorage] Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.warning(f"[ProfileStorage] Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[dict]:
        """
        List all saved sessions.
        
        Returns:
            List of session metadata
        """
        sessions = []
        
        for filepath in self.sessions_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "saved_at": data["saved_at"],
                    "phase": data.get("session_state", {}).get("phase", "unknown"),
                    "responses": len(data.get("session_state", {}).get("responses", [])),
                })
            except Exception as e:
                logger.warning(f"[ProfileStorage] Error reading session {filepath}: {e}")
        
        # Sort by saved_at, most recent first
        sessions.sort(key=lambda s: s["saved_at"], reverse=True)
        return sessions
    
    # =========================================================================
    # EXPORT/IMPORT
    # =========================================================================
    
    def export_profile(
        self, 
        slot_id: str, 
        export_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Export a profile to a shareable JSON file.
        
        Args:
            slot_id: The slot to export
            export_name: Name for the export file (optional)
        
        Returns:
            Path to the exported file, or None if failed
        """
        profile = self.load_profile(slot_id)
        if not profile:
            return None
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name = export_name or profile.slot.name.replace(" ", "_")
        filename = f"{name}_{timestamp}.json"
        filepath = self.exports_dir / filename
        
        export_data = {
            "format": "sovereign_profile_v1",
            "exported_at": datetime.utcnow().isoformat(),
            "profile": profile.to_dict(),
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[ProfileStorage] Exported profile to: {filepath}")
        return str(filepath)
    
    def import_profile(
        self, 
        filepath: str, 
        slot_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Import a profile from a JSON file.
        
        Args:
            filepath: Path to the export file
            slot_id: Specific slot to import to (or auto-assign)
        
        Returns:
            The slot_id where imported, or None if failed
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if data.get("format") != "sovereign_profile_v1":
                logger.error(f"[ProfileStorage] Invalid export format")
                return None
            
            profile = SavedProfile.from_dict(data["profile"])
            
            # Save to new slot
            return self.save_profile(
                session_state=profile.session_state,
                name=profile.slot.name,
                digital_twin=profile.digital_twin,
                slot_id=slot_id,
            )
            
        except Exception as e:
            logger.error(f"[ProfileStorage] Import error: {e}")
            return None
    
    def list_exports(self) -> List[dict]:
        """
        List all export files.
        
        Returns:
            List of export file metadata
        """
        exports = []
        
        for filepath in self.exports_dir.glob("*.json"):
            try:
                # Just get basic info without loading full file
                stat = filepath.stat()
                exports.append({
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception as e:
                logger.warning(f"[ProfileStorage] Error reading export {filepath}: {e}")
        
        # Sort by creation time, most recent first
        exports.sort(key=lambda e: e["created_at"], reverse=True)
        return exports


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_storage_instance: Optional[ProfileStorage] = None


def get_profile_storage() -> ProfileStorage:
    """
    Get the singleton ProfileStorage instance.
    
    Returns:
        The global ProfileStorage instance
    """
    global _storage_instance
    
    if _storage_instance is None:
        _storage_instance = ProfileStorage()
    
    return _storage_instance
