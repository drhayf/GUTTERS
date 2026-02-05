#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script: Show EXACTLY what JWT pywebpush is generating
"""

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path
import os
from dotenv import load_dotenv
from pywebpush import webpush
from py_vapid import Vapid02
import base64
import json
import jwt

project_root = Path(__file__).parent.parent
env_path = project_root / "src" / ".env"
load_dotenv(env_path)

private_key_b64 = os.getenv("VAPID_PRIVATE_KEY")
public_key_b64 = os.getenv("VAPID_PUBLIC_KEY")
claims_email = os.getenv("VAPID_CLAIM_EMAIL")

print("=" * 70)
print("VAPID JWT DEBUG")
print("=" * 70)
print()

print("ENVIRONMENT LOADED:")
print(f"VAPID_PRIVATE_KEY (first 30 chars): {private_key_b64[:30] if private_key_b64 else 'MISSING'}")
print(f"VAPID_PUBLIC_KEY: {public_key_b64}")
print(f"VAPID_CLAIM_EMAIL: {claims_email}")
print()

# Try to generate JWT directly with py-vapid
print("Attempting JWT generation with py-vapid:")
print("-" * 70)

try:
    vapid = Vapid02()

    # Try from_pem for PEM format keys
    if private_key_b64.startswith("-----BEGIN"):
        vapid.from_pem(private_key_b64 if isinstance(private_key_b64, bytes) else private_key_b64.encode())
        print("OK - Key loaded as PEM format")
    else:
        vapid.from_string(private_key_b64)
        print("OK - Key loaded as base64url raw format")

    # Generate VAPID claims
    vapid_claims = {
        "sub": claims_email or "mailto:admin@gutters.local",
        "aud": "https://fcm.googleapis.com",
        "exp": int(__import__("time").time()) + 3600,
    }

    # Generate JWT
    headers = vapid.sign(vapid_claims)

    print("OK - VAPID headers generated:")
    for key, val in headers.items():
        print(f"  {key}: {val[:50] if len(str(val)) > 50 else val}...")

    # Decode and show JWT contents
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        jwt_token = auth_header[7:]
        print(f"\nJWT Token (first 50 chars): {jwt_token[:50]}...")

        # Decode UNVERIFIED (for debugging)
        try:
            decoded = jwt.decode(jwt_token, options={"verify_signature": False})
            print(f"\nJWT Decoded (unverified):")
            print(json.dumps(decoded, indent=2))
        except Exception as e:
            print(f"Error decoding: {e}")

    print("\n" + "OK" * 20)
    print("VAPID keys CAN generate valid JWTs with py-vapid!")

except Exception as e:
    print(f"\nERROR: {e}")
    print(f"Type: {type(e).__name__}")
    import traceback

    traceback.print_exc()

print()
print("=" * 70)
