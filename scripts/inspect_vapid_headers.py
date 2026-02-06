#!/usr/bin/env python3
"""
Inspect exactly what VAPID headers are being generated and decode the JWT.
"""

import base64
import json
import os
import sys

# Change to src directory for proper imports
os.chdir(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.getcwd())

from app.core.config import settings
from app.modules.infrastructure.push.service import generate_vapid_headers


def decode_jwt(token):
    """Decode JWT without verification."""
    parts = token.split(".")
    if len(parts) != 3:
        return None

    def decode_part(part):
        # Add padding if needed
        padding = 4 - len(part) % 4
        if padding != 4:
            part += "=" * padding
        return json.loads(base64.urlsafe_b64decode(part))

    return {"header": decode_part(parts[0]), "payload": decode_part(parts[1]), "signature": parts[2]}


# Test with Apple endpoint
endpoint = "https://web.push.apple.com/test123"

print("=" * 60)
print("VAPID HEADER INSPECTION")
print("=" * 60)

# Generate headers
vapid_headers = generate_vapid_headers(
    settings.VAPID_PRIVATE_KEY.replace("\\n", "\n"), settings.RESOLVED_VAPID_SUB, endpoint
)

print("\n1. GENERATED HEADERS:")
print("-" * 60)
for key, value in vapid_headers.items():
    print(f"{key}: {value}")

# Extract and decode JWT
auth_header = vapid_headers.get("Authorization", "")
if auth_header.startswith("Bearer "):
    token = auth_header[7:]  # Remove "Bearer "

    print("\n2. DECODED JWT:")
    print("-" * 60)
    decoded = decode_jwt(token)
    print(f"Header:  {json.dumps(decoded['header'], indent=2)}")
    print(f"Payload: {json.dumps(decoded['payload'], indent=2)}")
    print(f"Signature (b64): {decoded['signature'][:50]}...")

    # Validate JWT structure
    print("\n3. JWT VALIDATION:")
    print("-" * 60)
    checks = [
        (decoded["header"].get("alg") == "ES256", "Algorithm is ES256"),
        (decoded["header"].get("typ") == "JWT", "Type is JWT"),
        ("sub" in decoded["payload"], "Has 'sub' claim"),
        ("aud" in decoded["payload"], "Has 'aud' claim"),
        ("iat" in decoded["payload"], "Has 'iat' claim"),
        ("exp" in decoded["payload"], "Has 'exp' claim"),
        (decoded["payload"].get("aud") == "gutters.local", "Audience is 'gutters.local'"),
        (decoded["payload"].get("sub") == "mailto:admin@gutters.local", "Subject matches"),
    ]

    for passed, desc in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {desc}")
        if not passed and "aud" in desc:
            print(f"       Got: {decoded['payload'].get('aud')}")

# Validate Crypto-Key header
print("\n4. CRYPTO-KEY HEADER:")
print("-" * 60)
crypto_key = vapid_headers.get("Crypto-Key", "")
if crypto_key.startswith("p256ecdsa="):
    public_key_b64 = crypto_key[10:]
    print(f"Public key (base64url): {public_key_b64}")
    print(f"Config public key:      {settings.VAPID_PUBLIC_KEY}")
    print(f"Match: {public_key_b64 == settings.VAPID_PUBLIC_KEY}")
else:
    print(f"[ERROR] Crypto-Key doesn't start with 'p256ecdsa=': {crypto_key}")

print("\n5. FINAL CHECK:")
print("-" * 60)
print("These headers would be sent to Apple:")
print(f"  Authorization: Bearer <{len(token)} char JWT>")
print(f"  Crypto-Key: p256ecdsa=<{len(public_key_b64)} char key>")
print("\nIf Apple rejects this, it's likely:")
print("  1. Subscription was created with different VAPID key")
print("  2. Domain mismatch (using gutters.local)")
print("  3. Subscription endpoint is invalid/expired")
print("=" * 60)
