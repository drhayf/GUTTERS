"""
Identity System - Persistent User Identity

This module manages the persistent identity of the user:
- Identity: The user's profile persisted across sessions
- IdentitySession: A session linked to an identity
- IdentityStore: Storage and retrieval of identities

Key Principle: Identity-Centric Storage
Unlike session-centric storage where data is tied to a session,
identity-centric storage ties data to the USER. Sessions come and go,
but the identity persists and evolves.

@module Identity
"""

from .store import (
    IdentityStore,
    get_identity_store,
)
from .identity import (
    Identity,
    IdentityMetadata,
)
from .session import (
    IdentitySession,
    SessionContext,
)

__all__ = [
    "IdentityStore",
    "get_identity_store",
    "Identity",
    "IdentityMetadata",
    "IdentitySession",
    "SessionContext",
]
