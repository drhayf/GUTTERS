"""
Storage Module - Persistent Profile and Session Storage

This module provides file-based storage for:
- Completed Digital Twin profiles
- In-progress session state
- Profile presets/templates

Follows the Fractal Extensibility Pattern with clear separation:
- profiles/ - Storage for completed profiles
- sessions/ - Storage for in-progress sessions
- exports/ - JSON exports for sharing
"""

from .profile_storage import (
    ProfileStorage,
    SavedProfile,
    ProfileSlot,
    get_profile_storage,
)

__all__ = [
    "ProfileStorage",
    "SavedProfile",
    "ProfileSlot",
    "get_profile_storage",
]
