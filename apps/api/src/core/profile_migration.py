"""
Profile Migration Layer - Legacy to New Digital Twin

This module handles migration from:
- Old: ProfileRubric, GenesisState, SavedProfile
- New: Identity, Trait, Domain system

Migration Strategy:
━━━━━━━━━━━━━━━━━━━━

1. DETECT: Check if legacy data exists
2. PARSE: Read legacy ProfileRubric structure
3. MAP: Convert to new Trait-based model
4. MIGRATE: Create Identity with converted traits
5. VERIFY: Validate migration completeness
6. CLEANUP: Optionally archive legacy data

Trait Mapping:
━━━━━━━━━━━━━━

Legacy ProfileRubric Field    →    New Trait Path
─────────────────────────────────────────────────
hd_type                       →    genesis.hd_type
hd_strategy                   →    genesis.hd_strategy
hd_authority                  →    genesis.hd_authority
hd_profile                    →    genesis.hd_profile
hd_centers                    →    genesis.hd_centers
jung_dominant                 →    genesis.jung_dominant
jung_auxiliary                →    genesis.jung_auxiliary
jung_tertiary                 →    genesis.jung_tertiary
jung_inferior                 →    genesis.jung_inferior
energy_pattern                →    genesis.energy_pattern
communication_style           →    genesis.communication_style
decision_pattern              →    genesis.decision_pattern
... (all other fields)

@module ProfileMigration
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


# =============================================================================
# LEGACY DATA STRUCTURES (for reference and parsing)
# =============================================================================

@dataclass
class LegacyTrait:
    """Structure of traits in old ProfileRubric."""
    value: Any
    confidence: float
    source: str
    evidence: List[str]
    detected_at: str


@dataclass
class LegacyProfileRubric:
    """
    The old ProfileRubric structure.
    Used as reference for migration.
    """
    # Human Design
    hd_type: Optional[LegacyTrait] = None
    hd_strategy: Optional[LegacyTrait] = None
    hd_authority: Optional[LegacyTrait] = None
    hd_profile: Optional[LegacyTrait] = None
    hd_definition: Optional[LegacyTrait] = None
    hd_centers: Optional[Dict[str, LegacyTrait]] = None
    
    # Jungian
    jung_dominant: Optional[LegacyTrait] = None
    jung_auxiliary: Optional[LegacyTrait] = None
    jung_tertiary: Optional[LegacyTrait] = None
    jung_inferior: Optional[LegacyTrait] = None
    jung_shadow: Optional[List[str]] = None
    mbti_type: Optional[LegacyTrait] = None
    
    # Energy & Patterns
    energy_pattern: Optional[LegacyTrait] = None
    rest_pattern: Optional[LegacyTrait] = None
    peak_hours: Optional[LegacyTrait] = None
    
    # Communication
    communication_style: Optional[LegacyTrait] = None
    learning_style: Optional[LegacyTrait] = None
    
    # Decision Making
    decision_pattern: Optional[LegacyTrait] = None
    risk_orientation: Optional[LegacyTrait] = None
    
    # Relationships
    relationship_pattern: Optional[LegacyTrait] = None
    attachment_style: Optional[LegacyTrait] = None
    
    # Core Patterns
    core_values: Optional[List[str]] = None
    core_fears: Optional[List[str]] = None
    core_desires: Optional[List[str]] = None
    life_themes: Optional[List[str]] = None
    
    # Metadata
    completion_percentage: float = 0.0
    total_interactions: int = 0


# =============================================================================
# MIGRATION MAPPING
# =============================================================================

# Maps legacy field names to new trait paths and categories
FIELD_MAPPING = {
    # Human Design fields
    "hd_type": ("genesis.hd_type", "human_design", "human_design"),
    "hd_strategy": ("genesis.hd_strategy", "human_design", "human_design"),
    "hd_authority": ("genesis.hd_authority", "human_design", "human_design"),
    "hd_profile": ("genesis.hd_profile", "human_design", "human_design"),
    "hd_definition": ("genesis.hd_definition", "human_design", "human_design"),
    "hd_not_self_theme": ("genesis.hd_not_self_theme", "human_design", "human_design"),
    "hd_signature": ("genesis.hd_signature", "human_design", "human_design"),
    
    # Jungian fields
    "jung_dominant": ("genesis.jung_dominant", "jungian", "jungian_cognitive"),
    "jung_auxiliary": ("genesis.jung_auxiliary", "jungian", "jungian_cognitive"),
    "jung_tertiary": ("genesis.jung_tertiary", "jungian", "jungian_cognitive"),
    "jung_inferior": ("genesis.jung_inferior", "jungian", "jungian_cognitive"),
    "mbti_type": ("genesis.mbti_type", "mbti", "mbti"),
    
    # Energy patterns
    "energy_pattern": ("genesis.energy_pattern", "somatic", "somatic"),
    "rest_pattern": ("genesis.rest_pattern", "somatic", "somatic"),
    "peak_hours": ("genesis.peak_hours", "somatic", "somatic"),
    
    # Communication
    "communication_style": ("genesis.communication_style", "behavioral", "core_patterns"),
    "learning_style": ("genesis.learning_style", "behavioral", "core_patterns"),
    "emotional_expression": ("genesis.emotional_expression", "emotional", "core_patterns"),
    "conflict_style": ("genesis.conflict_style", "behavioral", "core_patterns"),
    
    # Decision making
    "decision_pattern": ("genesis.decision_pattern", "cognitive", "core_patterns"),
    "risk_orientation": ("genesis.risk_orientation", "cognitive", "core_patterns"),
    "planning_style": ("genesis.planning_style", "cognitive", "core_patterns"),
    
    # Relationships
    "relationship_pattern": ("genesis.relationship_pattern", "relational", "core_patterns"),
    "attachment_style": ("genesis.attachment_style", "relational", "core_patterns"),
    "love_language": ("genesis.love_language", "relational", "core_patterns"),
    
    # Core patterns (arrays)
    "core_values": ("genesis.core_values", "values", "core_patterns"),
    "core_fears": ("genesis.core_fears", "shadow", "jungian_shadow"),
    "core_desires": ("genesis.core_desires", "motivational", "core_patterns"),
    "life_themes": ("genesis.life_themes", "existential", "core_patterns"),
    "growth_edges": ("genesis.growth_edges", "developmental", "core_patterns"),
    "blind_spots": ("genesis.blind_spots", "shadow", "jungian_shadow"),
    "superpowers": ("genesis.superpowers", "strengths", "core_patterns"),
}


# =============================================================================
# MIGRATION ENGINE
# =============================================================================

@dataclass
class MigrationResult:
    """Result of a profile migration."""
    success: bool
    identity_id: Optional[str] = None
    traits_migrated: int = 0
    traits_failed: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ProfileMigrator:
    """
    Migrates legacy profile data to the new Digital Twin system.
    
    Usage:
        migrator = ProfileMigrator()
        
        # Migrate from saved profile
        result = await migrator.migrate_saved_profile(slot_id="1")
        
        # Migrate from raw data
        result = await migrator.migrate_rubric_data(legacy_data)
        
        # Check migration status
        if result.success:
            print(f"Migrated {result.traits_migrated} traits")
    """
    
    def __init__(self):
        self._digital_twin = None
    
    async def _get_twin(self):
        """Get Digital Twin core."""
        if self._digital_twin is None:
            from ..digital_twin import get_digital_twin_core
            self._digital_twin = await get_digital_twin_core()
        return self._digital_twin
    
    async def migrate_saved_profile(
        self,
        slot_id: str,
        storage_path: str = "data"
    ) -> MigrationResult:
        """
        Migrate a saved profile from the old storage format.
        
        Args:
            slot_id: The profile slot ID (e.g., "1", "2")
            storage_path: Path to the data directory
        
        Returns:
            MigrationResult with status and details
        """
        result = MigrationResult(success=False)
        
        try:
            # Load the saved profile
            profile_path = Path(storage_path) / "profiles" / f"slot_{slot_id}.json"
            
            if not profile_path.exists():
                result.errors.append(f"Profile not found: {profile_path}")
                return result
            
            with open(profile_path, 'r') as f:
                saved_data = json.load(f)
            
            # Extract session state
            session_state = saved_data.get("session_state", {})
            digital_twin_legacy = saved_data.get("digital_twin", {})
            
            # Get rubric data from session state or digital twin
            rubric_data = session_state.get("rubric") or session_state.get("profile_rubric")
            if not rubric_data and digital_twin_legacy:
                rubric_data = digital_twin_legacy
            
            if not rubric_data:
                result.errors.append("No rubric data found in saved profile")
                return result
            
            # Migrate the rubric
            result = await self.migrate_rubric_data(
                rubric_data,
                metadata={
                    "source": "saved_profile",
                    "slot_id": slot_id,
                    "migrated_at": datetime.now().isoformat(),
                    "original_completion": saved_data.get("slot", {}).get("completion_percentage", 0),
                }
            )
            
            # Archive the old profile
            if result.success:
                await self._archive_legacy_profile(profile_path)
            
            return result
            
        except Exception as e:
            logger.error(f"[ProfileMigrator] Error migrating saved profile: {e}")
            result.errors.append(str(e))
            return result
    
    async def migrate_rubric_data(
        self,
        rubric_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MigrationResult:
        """
        Migrate raw ProfileRubric data to new system.
        
        Args:
            rubric_data: The legacy rubric dictionary
            metadata: Optional migration metadata
        
        Returns:
            MigrationResult with status and details
        """
        result = MigrationResult(success=False)
        
        try:
            twin = await self._get_twin()
            
            # Create or get identity
            identity_id = metadata.get("identity_id") if metadata else None
            if not identity_id:
                # Create new identity
                identity = await twin.create_identity()
                identity_id = identity.id
            
            result.identity_id = identity_id
            
            # Migrate each field
            for field_name, field_data in rubric_data.items():
                if field_name in ["completion_percentage", "total_interactions"]:
                    continue  # Skip metadata fields
                
                try:
                    migrated = await self._migrate_field(
                        twin, field_name, field_data, identity_id
                    )
                    if migrated:
                        result.traits_migrated += 1
                    else:
                        result.traits_failed += 1
                        result.warnings.append(f"Could not migrate field: {field_name}")
                except Exception as e:
                    result.traits_failed += 1
                    result.warnings.append(f"Error migrating {field_name}: {e}")
            
            # Store migration metadata
            await twin.set(
                path="system.migration_info",
                value={
                    "migrated_at": datetime.now().isoformat(),
                    "source": metadata.get("source", "unknown") if metadata else "unknown",
                    "traits_migrated": result.traits_migrated,
                    "original_completion": rubric_data.get("completion_percentage", 0),
                },
                source="migration"
            )
            
            result.success = True
            logger.info(
                f"[ProfileMigrator] Migrated {result.traits_migrated} traits "
                f"to identity {identity_id}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[ProfileMigrator] Migration error: {e}")
            result.errors.append(str(e))
            return result
    
    async def _migrate_field(
        self,
        twin,
        field_name: str,
        field_data: Any,
        identity_id: str
    ) -> bool:
        """Migrate a single field from legacy to new format."""
        
        # Get mapping info
        mapping = FIELD_MAPPING.get(field_name)
        if not mapping:
            logger.debug(f"[ProfileMigrator] No mapping for field: {field_name}")
            return False
        
        trait_path, category, framework = mapping
        
        # Parse legacy trait data
        if isinstance(field_data, dict):
            # Full trait object
            value = field_data.get("value")
            confidence = field_data.get("confidence", 0.5)
            evidence = field_data.get("evidence", [])
            source = field_data.get("source", "migration")
        elif isinstance(field_data, list):
            # Array value (e.g., core_values)
            value = field_data
            confidence = 0.7  # Default for arrays
            evidence = []
            source = "migration"
        else:
            # Simple value
            value = field_data
            confidence = 0.5
            evidence = []
            source = "migration"
        
        if value is None:
            return False
        
        # Set the trait in new system
        await twin.set(
            path=trait_path,
            value=value,
            confidence=confidence,
            source=f"migration:{source}",
            metadata={
                "category": category,
                "framework": framework,
                "evidence": evidence,
                "migrated_from": field_name,
                "migrated_at": datetime.now().isoformat(),
            }
        )
        
        return True
    
    async def _archive_legacy_profile(self, profile_path: Path) -> None:
        """Archive a legacy profile after migration."""
        try:
            archive_dir = profile_path.parent / "archived"
            archive_dir.mkdir(exist_ok=True)
            
            archive_path = archive_dir / f"{profile_path.stem}_migrated.json"
            
            # Read and add migration note
            with open(profile_path, 'r') as f:
                data = json.load(f)
            
            data["_migration_note"] = {
                "migrated_at": datetime.now().isoformat(),
                "archived_from": str(profile_path),
            }
            
            with open(archive_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"[ProfileMigrator] Archived legacy profile to {archive_path}")
            
        except Exception as e:
            logger.warning(f"[ProfileMigrator] Could not archive profile: {e}")
    
    async def migrate_all_profiles(
        self,
        storage_path: str = "data"
    ) -> Dict[str, MigrationResult]:
        """
        Migrate all saved profiles.
        
        Returns:
            Dict mapping slot_id to MigrationResult
        """
        results = {}
        profiles_dir = Path(storage_path) / "profiles"
        
        if not profiles_dir.exists():
            logger.info("[ProfileMigrator] No profiles directory found")
            return results
        
        for profile_file in profiles_dir.glob("slot_*.json"):
            slot_id = profile_file.stem.replace("slot_", "")
            logger.info(f"[ProfileMigrator] Migrating profile slot {slot_id}")
            
            result = await self.migrate_saved_profile(slot_id, storage_path)
            results[slot_id] = result
        
        # Summary
        total = len(results)
        success = sum(1 for r in results.values() if r.success)
        logger.info(f"[ProfileMigrator] Migration complete: {success}/{total} successful")
        
        return results
    
    async def check_migration_status(
        self,
        storage_path: str = "data"
    ) -> Dict[str, Any]:
        """
        Check which profiles need migration.
        
        Returns:
            Status dict with profiles needing migration
        """
        profiles_dir = Path(storage_path) / "profiles"
        archived_dir = profiles_dir / "archived" if profiles_dir.exists() else None
        
        needs_migration = []
        already_migrated = []
        
        if profiles_dir.exists():
            for profile_file in profiles_dir.glob("slot_*.json"):
                slot_id = profile_file.stem.replace("slot_", "")
                needs_migration.append(slot_id)
        
        if archived_dir and archived_dir.exists():
            for archive_file in archived_dir.glob("*_migrated.json"):
                slot_id = archive_file.stem.replace("slot_", "").replace("_migrated", "")
                already_migrated.append(slot_id)
        
        return {
            "needs_migration": needs_migration,
            "already_migrated": already_migrated,
            "total_profiles": len(needs_migration),
            "total_migrated": len(already_migrated),
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_migrator: Optional[ProfileMigrator] = None


def get_migrator() -> ProfileMigrator:
    """Get the ProfileMigrator instance."""
    global _migrator
    if _migrator is None:
        _migrator = ProfileMigrator()
    return _migrator


async def migrate_profile(slot_id: str) -> MigrationResult:
    """Quick migration of a single profile."""
    return await get_migrator().migrate_saved_profile(slot_id)


async def migrate_all() -> Dict[str, MigrationResult]:
    """Quick migration of all profiles."""
    return await get_migrator().migrate_all_profiles()
