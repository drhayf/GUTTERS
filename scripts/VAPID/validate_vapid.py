#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAPID Key Pair Validation Script

Diagnoses "BadJwtToken" errors by cryptographically verifying that:
1. VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY match
2. Keys are properly formatted
3. VAPID headers can be generated successfully
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Optional
import base64

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from cryptography.hazmat.primitives.serialization import (
        load_pem_private_key,
        Encoding,
        PublicFormat,
        PrivateFormat,
        NoEncryption,
    )
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import ec
    from pywebpush import webpush
    from py_vapid import Vapid02
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install with: pip install pywebpush py-vapid cryptography")
    sys.exit(1)


def load_env() -> Tuple[str, str, Optional[str]]:
    """Load VAPID keys from .env file."""
    env_paths = [
        project_root / "src" / ".env",
        project_root / ".env",
    ]

    env_path = None
    for path in env_paths:
        if path.exists():
            env_path = path
            break

    if not env_path:
        print(f"❌ .env file not found. Checked:")
        for path in env_paths:
            print(f"   - {path}")
        sys.exit(1)

    private_key = None
    public_key = None
    mailto = None

    # Read entire file
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parse line by line, handling multi-line PEM keys
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Handle VAPID_PRIVATE_KEY (potentially multi-line PEM)
        if line.startswith("VAPID_PRIVATE_KEY="):
            value = line.split("=", 1)[1].strip()
            # Check if it's a multi-line PEM key
            if value.startswith('"-----BEGIN PRIVATE KEY-----'):
                # Collect all lines until we find the closing quote
                pem_lines = [value.strip('"')]
                i += 1
                while i < len(lines):
                    next_line = lines[i].rstrip("\n").rstrip("\r")
                    if next_line.rstrip().endswith('"'):
                        pem_lines.append(next_line.rstrip('"'))
                        break
                    else:
                        pem_lines.append(next_line)
                    i += 1
                private_key = "\n".join(pem_lines)
                # Convert escaped newlines to actual newlines
                private_key = private_key.replace("\\n", "\n")
            else:
                # Single line key
                private_key = value.strip('"').strip("'")
                # Convert escaped newlines to actual newlines
                private_key = private_key.replace("\\n", "\n")

        # Handle VAPID_PUBLIC_KEY
        elif line.startswith("VAPID_PUBLIC_KEY="):
            public_key = line.split("=", 1)[1].strip('"').strip("'")

        # Handle mailto claim
        elif line.startswith("VAPID_CLAIM_EMAIL=") or line.startswith("VAPID_CLAIMS_SUB="):
            mailto = line.split("=", 1)[1].strip('"').strip("'")

        i += 1

    if not private_key:
        print("❌ VAPID_PRIVATE_KEY not found in .env")
        sys.exit(1)

    if not public_key:
        print("❌ VAPID_PUBLIC_KEY not found in .env")
        sys.exit(1)

    print(f"✅ Loaded keys from {env_path}")
    print(f"   Private key length: {len(private_key)} chars")
    print(f"   Public key length: {len(public_key)} chars")
    print(f"   Mailto claim: {mailto or 'NOT SET'}\n")

    return private_key, public_key, mailto


def derive_public_from_private(private_key: str) -> Optional[str]:
    """Derive public key from private key using cryptography library."""
    try:
        # Load private key (PEM format)
        key_obj = load_pem_private_key(private_key.encode("utf-8"), password=None, backend=default_backend())

        # Extract public key in X962 uncompressed format
        public_key_raw = key_obj.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)

        # Convert to base64url (VAPID format)
        public_key_b64 = base64.urlsafe_b64encode(public_key_raw).decode().rstrip("=")

        print(f"✅ Private key is valid (PEM format)")
        return public_key_b64

    except Exception as e:
        print(f"❌ Failed to parse private key: {e}")
        return None


def normalize_key(key: str) -> str:
    """Normalize key format for comparison (remove whitespace, padding)."""
    return key.replace(" ", "").replace("\n", "").rstrip("=").lower()


def generate_new_keypair() -> Tuple[str, str]:
    """Generate a new VAPID key pair."""
    # Generate EC key pair
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Export private key as PEM
    private_pem = (
        private_key.private_bytes(
            encoding=Encoding.PEM, format=PrivateFormat.PKCS8, encryption_algorithm=NoEncryption()
        )
        .decode("utf-8")
        .strip()
    )

    # Export public key as base64url
    public_raw = private_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    public_b64 = base64.urlsafe_b64encode(public_raw).decode().rstrip("=")

    return private_pem, public_b64


def test_vapid_headers(private_key: str, mailto: Optional[str]) -> bool:
    """Test if VAPID headers can be generated successfully."""
    if not mailto or mailto == "NOT SET":
        print("⚠️  VAPID_CLAIM_EMAIL not set in .env")
        print("   This MUST be set to 'mailto:your-email@example.com'")
        return False

    try:
        vapid = Vapid02()
        vapid.from_pem(private_key.encode("utf-8"))

        # Generate VAPID claims
        vapid_claims = {
            "sub": mailto if mailto.startswith("mailto:") else f"mailto:{mailto}",
            "aud": "https://fcm.googleapis.com",  # Test with FCM endpoint
        }

        headers = vapid.sign(vapid_claims)

        print(f"✅ VAPID headers generated successfully")
        print(f"   Authorization: {headers.get('Authorization', 'N/A')[:60]}...")
        print(f"   Crypto-Key: {headers.get('Crypto-Key', 'N/A')[:60]}...")
        return True

    except Exception as e:
        print(f"❌ Failed to generate VAPID headers: {e}")
        return False


def main():
    """Run VAPID validation diagnostics."""
    print("=" * 70)
    print("VAPID KEY PAIR VALIDATION")
    print("=" * 70)
    print()

    # Step 1: Load keys from .env
    print("STEP 1: Loading keys from .env")
    print("-" * 70)
    private_key, public_key, mailto = load_env()

    # Step 2: Derive public key from private key
    print("STEP 2: Deriving public key from private key")
    print("-" * 70)
    derived_public = derive_public_from_private(private_key)

    if not derived_public:
        print("\n" + "=" * 70)
        print("RESULT: CRITICAL - Private key is malformed")
        print("=" * 70)
        print("\nGenerating NEW key pair...\n")

        new_private, new_public = generate_new_keypair()

        print("🔑 NEW VAPID KEY PAIR GENERATED")
        print("=" * 70)
        print("\nReplace these in your .env file:\n")
        print(f'VAPID_PRIVATE_KEY="{new_private}"')
        print(f'VAPID_PUBLIC_KEY="{new_public}"')

        if not mailto or mailto == "NOT SET":
            print(f'VAPID_CLAIM_EMAIL="mailto:your-email@example.com"')

        print("\n" + "=" * 70)
        return

    # Step 3: Compare keys
    print("\nSTEP 3: Comparing derived vs loaded public key")
    print("-" * 70)

    # Normalize both keys for comparison
    derived_normalized = normalize_key(derived_public)
    loaded_normalized = normalize_key(public_key)

    print(f"Derived: {derived_normalized[:64]}...")
    print(f"Loaded:  {loaded_normalized[:64]}...")

    if derived_normalized == loaded_normalized:
        print("\n✅ PUBLIC KEYS MATCH - Key pair is valid!")
        keys_valid = True
    else:
        print("\n❌ PUBLIC KEYS DO NOT MATCH - Key pair is broken!")
        print(f"\nFull comparison:")
        print(f"  Derived length: {len(derived_normalized)}")
        print(f"  Loaded length:  {len(loaded_normalized)}")
        keys_valid = False

    # Step 4: Test VAPID header generation
    print("\nSTEP 4: Testing VAPID header generation")
    print("-" * 70)
    headers_valid = test_vapid_headers(private_key, mailto)

    # Final result
    print("\n" + "=" * 70)
    print("FINAL DIAGNOSIS")
    print("=" * 70)

    if keys_valid:
        print("\n✅ KEYS ARE VALID AND WORKING")
        print("\nThe VAPID key pair is correctly configured!")
        print("If you're still seeing BadJwtToken errors, check:")
        print("  1. Restart the backend server to load new keys")
        print("  2. Clear browser storage and re-subscribe in the frontend")
        print("  3. Verify the public key endpoint returns the new public key")
        print("  4. Check subscription endpoint matches the 'aud' claim")

        if headers_valid:
            print("\n✅ VAPID header generation also successful!")
        else:
            print("\n⚠️  VAPID header test failed but keys are valid")
            print("   This might be a py-vapid library issue, not your keys")

    else:
        print("\n❌ KEYS ARE INVALID OR MISMATCHED")
        print("\nGenerating NEW key pair...\n")

        new_private, new_public = generate_new_keypair()

        print("🔑 NEW VAPID KEY PAIR GENERATED")
        print("=" * 70)
        print("\nReplace these in your .env file:\n")
        print(f'VAPID_PRIVATE_KEY="{new_private}"')
        print(f'VAPID_PUBLIC_KEY="{new_public}"')

        if not mailto or mailto == "NOT SET":
            print(f'VAPID_CLAIM_EMAIL="mailto:your-email@example.com"')

        print("\n⚠️  After updating .env:")
        print("  1. Restart the backend server")
        print("  2. Clear browser storage and re-subscribe to push notifications")
        print("  3. The public key endpoint must return the NEW public key")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
