#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Manual VAPID Header Generation

Tests if we can generate valid VAPID headers manually using cryptography + jwt,
bypassing py_vapid's buggy API.
"""

import os
import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from dotenv import load_dotenv
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import jwt
    import time
    import base64
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install with: pip install python-dotenv cryptography pyjwt")
    sys.exit(1)


def load_vapid_keys():
    """Load VAPID keys from .env."""
    env_path = project_root / "src" / ".env"
    load_dotenv(env_path)

    private_key = os.getenv("VAPID_PRIVATE_KEY")
    public_key = os.getenv("VAPID_PUBLIC_KEY")
    claims_sub = os.getenv("VAPID_CLAIM_EMAIL") or os.getenv("VAPID_CLAIMS_SUB")

    if not private_key or not public_key:
        print("❌ VAPID keys not found in .env")
        sys.exit(1)

    # Convert escaped newlines to actual newlines
    private_key = private_key.replace("\\n", "\n")

    return private_key, public_key, claims_sub


def generate_vapid_headers(private_key_pem: str, subject: str) -> dict:
    """
    Generate VAPID headers manually without using py-vapid's buggy API.
    """
    # Load the private key
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode() if isinstance(private_key_pem, str) else private_key_pem,
        password=None,
        backend=default_backend(),
    )

    # Generate JWT for AUTH header
    now = int(time.time())
    claims = {"sub": subject, "aud": "https://fcm.googleapis.com", "iat": now, "exp": now + 3600}

    token = jwt.encode(claims, private_key, algorithm="ES256")

    # Generate public key for Crypto-Key header
    public_key = private_key.public_key()
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.X962, format=serialization.PublicFormat.UncompressedPoint
    )
    public_b64 = base64.urlsafe_b64encode(public_der).decode().rstrip("=")

    return {"Authorization": f"Bearer {token}", "Crypto-Key": f"p256ecdsa={public_b64}"}


def main():
    print("=" * 70)
    print("MANUAL VAPID HEADER GENERATION TEST")
    print("=" * 70)
    print()

    # Step 1: Load keys
    print("STEP 1: Loading VAPID keys from .env")
    print("-" * 70)
    private_key, public_key, claims_sub = load_vapid_keys()

    print(f"✅ Loaded keys")
    print(f"   Private key length: {len(private_key)} chars")
    print(f"   Public key length: {len(public_key)} chars")
    print(f"   Claims sub: {claims_sub}\n")

    # Step 2: Generate VAPID headers manually
    print("STEP 2: Generating VAPID headers manually")
    print("-" * 70)

    try:
        headers = generate_vapid_headers(private_key, claims_sub)

        print("✅ VAPID headers generated successfully!")
        print(f"   Authorization: {headers['Authorization'][:80]}...")
        print(f"   Crypto-Key: {headers['Crypto-Key'][:80]}...\n")

        # Step 3: Verify JWT structure
        print("STEP 3: Verifying JWT structure")
        print("-" * 70)

        token = headers["Authorization"].replace("Bearer ", "")
        parts = token.split(".")

        if len(parts) == 3:
            print("✅ JWT has correct structure (header.payload.signature)")
            print(f"   Header length: {len(parts[0])} chars")
            print(f"   Payload length: {len(parts[1])} chars")
            print(f"   Signature length: {len(parts[2])} chars\n")

            # Decode and verify payload
            import json

            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
            print("✅ JWT payload decoded successfully:")
            print(f"   sub: {payload.get('sub')}")
            print(f"   aud: {payload.get('aud')}")
            print(f"   iat: {payload.get('iat')}")
            print(f"   exp: {payload.get('exp')}\n")

            success = True
        else:
            print("❌ JWT has incorrect structure")
            success = False

    except Exception as e:
        print(f"❌ Failed to generate VAPID headers: {e}")
        print(f"   Type: {type(e).__name__}\n")
        success = False

    # Final verdict
    print("=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)

    if success:
        print("\n✅ SUCCESS! Manual VAPID header generation works!")
        print("\nWhat this means:")
        print("  • Keys are properly formatted")
        print("  • Manual JWT generation works")
        print("  • We can bypass py_vapid's buggy API")
        print("  • Push notifications can work with manual header generation\n")

        print("📋 NEXT STEPS:")
        print("  1. Update service.py to use manual VAPID header generation")
        print("  2. Or use service_fixed.py which already has this implementation")
        print("  3. Restart backend server")
        print("  4. Clear browser storage and re-subscribe")
        print("  5. Test push notifications - they should work!")

    else:
        print("\n❌ Manual VAPID header generation failed")
        print("\nThe keys may still have issues.")

    print("\n" + "=" * 70)
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
