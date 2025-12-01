"""
Identity Store - Persistent Storage for Identities

Manages saving and loading identities:
- File-based storage in data/identities/
- Identity lookup and listing
- Auto-save support
- Migration from old profile format

@module IdentityStore
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import json
import logging
import os

from .identity import Identity, IdentityMetadata, IdentityStatus
from .session import IdentitySession

logger = logging.getLogger(__name__)


class IdentityStore:
    """
    Persistent storage for user identities.
    
    Features:
    - File-based storage (JSON)
    - Identity listing and lookup
    - Session recovery
    - Auto-save support
    - Migration from legacy profile format
    
    File Structure:
        data/
        ├── identities/
        │   ├── {identity_id}.json   # Full identity data
        │   └── ...
        ├── sessions/
        │   ├── {session_id}.json    # Active session state
        │   └── ...
        └── metadata.json            # Index of all identities
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the identity store.
        
        Args:
            data_dir: Root directory for data. Defaults to api/data
        """
        if data_dir is None:
            api_dir = Path(__file__).parent.parent.parent.parent
            data_dir = api_dir / "data"
        else:
            data_dir = Path(data_dir)
        
        self.data_dir = data_dir
        self.identities_dir = data_dir / "identities"
        self.sessions_dir = data_dir / "sessions"
        self.metadata_path = data_dir / "identity_metadata.json"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Cache
        self._metadata_cache: Dict[str, IdentityMetadata] = {}
        self._load_metadata()
        
        logger.info(f"[IdentityStore] Initialized with data_dir: {self.data_dir}")
    
    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.identities_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    # -------------------------------------------------------------------------
    # Metadata Management
    # -------------------------------------------------------------------------
    
    def _load_metadata(self) -> None:
        """Load identity metadata index."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r") as f:
                    data = json.load(f)
                    for id_data in data.get("identities", []):
                        meta = IdentityMetadata.from_dict(id_data)
                        self._metadata_cache[meta.id] = meta
                logger.info(f"[IdentityStore] Loaded {len(self._metadata_cache)} identity metadata entries")
            except Exception as e:
                logger.error(f"[IdentityStore] Failed to load metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save identity metadata index."""
        try:
            data = {
                "version": 1,
                "updated_at": datetime.utcnow().isoformat(),
                "identities": [m.to_dict() for m in self._metadata_cache.values()],
            }
            with open(self.metadata_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[IdentityStore] Failed to save metadata: {e}")
    
    def _update_metadata(self, identity: Identity) -> None:
        """Update metadata cache for an identity."""
        self._metadata_cache[identity.id] = identity.get_metadata()
        self._save_metadata()
    
    # -------------------------------------------------------------------------
    # Identity Operations
    # -------------------------------------------------------------------------
    
    def save(self, identity: Identity) -> bool:
        """
        Save an identity to storage.
        
        Args:
            identity: The identity to save
        
        Returns:
            True if saved successfully
        """
        try:
            identity_path = self.identities_dir / f"{identity.id}.json"
            
            with open(identity_path, "w") as f:
                json.dump(identity.to_dict(), f, indent=2)
            
            self._update_metadata(identity)
            logger.info(f"[IdentityStore] Saved identity: {identity.id}")
            return True
            
        except Exception as e:
            logger.error(f"[IdentityStore] Failed to save identity {identity.id}: {e}")
            return False
    
    def load(self, identity_id: str) -> Optional[Identity]:
        """
        Load an identity from storage.
        
        Args:
            identity_id: The identity ID to load
        
        Returns:
            The loaded identity, or None if not found
        """
        identity_path = self.identities_dir / f"{identity_id}.json"
        
        if not identity_path.exists():
            logger.warning(f"[IdentityStore] Identity not found: {identity_id}")
            return None
        
        try:
            with open(identity_path, "r") as f:
                data = json.load(f)
            
            identity = Identity.from_dict(data)
            identity.last_accessed = datetime.utcnow()
            
            logger.info(f"[IdentityStore] Loaded identity: {identity_id}")
            return identity
            
        except Exception as e:
            logger.error(f"[IdentityStore] Failed to load identity {identity_id}: {e}")
            return None
    
    def delete(self, identity_id: str) -> bool:
        """
        Delete an identity from storage.
        
        Args:
            identity_id: The identity ID to delete
        
        Returns:
            True if deleted successfully
        """
        identity_path = self.identities_dir / f"{identity_id}.json"
        
        if not identity_path.exists():
            return False
        
        try:
            identity_path.unlink()
            
            if identity_id in self._metadata_cache:
                del self._metadata_cache[identity_id]
                self._save_metadata()
            
            logger.info(f"[IdentityStore] Deleted identity: {identity_id}")
            return True
            
        except Exception as e:
            logger.error(f"[IdentityStore] Failed to delete identity {identity_id}: {e}")
            return False
    
    def exists(self, identity_id: str) -> bool:
        """Check if an identity exists."""
        return (self.identities_dir / f"{identity_id}.json").exists()
    
    def list_identities(self) -> List[IdentityMetadata]:
        """
        List all identities.
        
        Returns metadata only (not full identity data).
        """
        return list(self._metadata_cache.values())
    
    def get_metadata(self, identity_id: str) -> Optional[IdentityMetadata]:
        """Get metadata for a specific identity."""
        return self._metadata_cache.get(identity_id)
    
    def create(self, name: str = "New Profile") -> Identity:
        """
        Create a new identity.
        
        Args:
            name: Display name for the identity
        
        Returns:
            The new identity (not yet saved)
        """
        identity = Identity(
            id=str(uuid4()),
            name=name,
            created_at=datetime.utcnow(),
        )
        return identity
    
    def get_or_create_default(self) -> Identity:
        """
        Get the default identity or create one if none exists.
        
        Returns:
            The default (first) identity
        """
        identities = self.list_identities()
        
        if identities:
            # Return most recently accessed
            identities.sort(key=lambda x: x.last_accessed, reverse=True)
            return self.load(identities[0].id)
        
        # Create default
        identity = self.create("My Profile")
        self.save(identity)
        return identity
    
    # -------------------------------------------------------------------------
    # Session Operations
    # -------------------------------------------------------------------------
    
    def save_session(self, session: IdentitySession) -> bool:
        """
        Save session state for recovery.
        
        Args:
            session: The session to save
        
        Returns:
            True if saved successfully
        """
        try:
            session_path = self.sessions_dir / f"{session.id}.json"
            
            with open(session_path, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            
            session.mark_saved()
            logger.debug(f"[IdentityStore] Saved session: {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"[IdentityStore] Failed to save session {session.id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[IdentitySession]:
        """
        Load a session from storage.
        
        Args:
            session_id: The session ID to load
        
        Returns:
            The loaded session, or None if not found
        """
        session_path = self.sessions_dir / f"{session_id}.json"
        
        if not session_path.exists():
            return None
        
        try:
            with open(session_path, "r") as f:
                data = json.load(f)
            
            return IdentitySession.from_dict(data)
            
        except Exception as e:
            logger.error(f"[IdentityStore] Failed to load session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        session_path = self.sessions_dir / f"{session_id}.json"
        
        if session_path.exists():
            try:
                session_path.unlink()
                return True
            except Exception:
                pass
        return False
    
    def get_active_sessions(self, identity_id: str) -> List[IdentitySession]:
        """Get all active sessions for an identity."""
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                
                if data.get("identity_id") == identity_id:
                    session = IdentitySession.from_dict(data)
                    if session.is_active:
                        sessions.append(session)
            except Exception:
                pass
        
        return sessions
    
    def cleanup_stale_sessions(self) -> int:
        """
        Remove stale session files.
        
        Returns:
            Number of sessions cleaned up
        """
        cleaned = 0
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                
                session = IdentitySession.from_dict(data)
                if session.is_stale or not session.is_active:
                    session_file.unlink()
                    cleaned += 1
            except Exception:
                # Delete corrupt files
                try:
                    session_file.unlink()
                    cleaned += 1
                except Exception:
                    pass
        
        if cleaned:
            logger.info(f"[IdentityStore] Cleaned up {cleaned} stale sessions")
        
        return cleaned
    
    # -------------------------------------------------------------------------
    # Migration
    # -------------------------------------------------------------------------
    
    def migrate_from_legacy_profile(self, legacy_data: Dict[str, Any]) -> Identity:
        """
        Migrate a legacy profile (ProfileRubric format) to Identity.
        
        Args:
            legacy_data: Data from old ProfileRubric/SavedProfile format
        
        Returns:
            New Identity with migrated data
        """
        from ..traits import Trait, TraitCategory, TraitFramework, TraitSource, SourceType
        
        identity = self.create("Migrated Profile")
        
        # Map legacy rubric fields to traits
        rubric = legacy_data.get("rubric", {})
        
        trait_mappings = [
            ("hd_type", "hd_type", TraitCategory.ENERGY, [TraitFramework.HUMAN_DESIGN]),
            ("hd_strategy", "hd_strategy", TraitCategory.BEHAVIOR, [TraitFramework.HUMAN_DESIGN]),
            ("hd_authority", "hd_authority", TraitCategory.COGNITION, [TraitFramework.HUMAN_DESIGN]),
            ("jung_dominant", "jung_dominant", TraitCategory.COGNITION, [TraitFramework.JUNGIAN]),
            ("jung_auxiliary", "jung_auxiliary", TraitCategory.COGNITION, [TraitFramework.JUNGIAN]),
            ("energy_pattern", "energy_pattern", TraitCategory.ENERGY, []),
            ("core_wound", "core_wound", TraitCategory.WOUND, []),
            ("core_gift", "core_gift", TraitCategory.GIFT, []),
            ("decision_style", "decision_style", TraitCategory.STYLE, []),
        ]
        
        for legacy_field, trait_name, category, frameworks in trait_mappings:
            if legacy_field in rubric:
                legacy_trait = rubric[legacy_field]
                if isinstance(legacy_trait, dict) and legacy_trait.get("value"):
                    trait = Trait.create(
                        name=trait_name,
                        value=legacy_trait["value"],
                        domain="genesis",
                        source_agent="migration",
                        confidence=legacy_trait.get("confidence", 0.5),
                        category=category,
                        frameworks=frameworks,
                        evidence=legacy_trait.get("evidence", []),
                    )
                    identity.set_trait(trait)
        
        # Migrate digital_twin data if present
        if "digital_twin" in legacy_data:
            dt = legacy_data["digital_twin"]
            if dt.get("essence_statement"):
                identity.essence_statement = dt["essence_statement"]
            if dt.get("archetypes"):
                identity.archetypes = dt["archetypes"]
        
        logger.info(f"[IdentityStore] Migrated legacy profile to identity: {identity.id}")
        return identity


# =============================================================================
# SINGLETON
# =============================================================================

_identity_store: Optional[IdentityStore] = None


def get_identity_store() -> IdentityStore:
    """Get the singleton identity store instance."""
    global _identity_store
    
    if _identity_store is None:
        _identity_store = IdentityStore()
    
    return _identity_store
