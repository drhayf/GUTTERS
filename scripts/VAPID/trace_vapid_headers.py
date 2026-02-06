#!/usr/bin/env python3
"""Trace how pywebpush generates VAPID headers with our keys."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load env
env_path = Path(__file__).parent.parent / "src" / ".env"
load_dotenv(env_path)

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "")

print("=" * 80)
print("TRACING VAPID HEADER GENERATION")
print("=" * 80)

print("\n1. INPUT KEYS:")
print(f"   Public Key (87 chars): {VAPID_PUBLIC_KEY[:50]}...")
print(f"   Private Key (240 chars): {VAPID_PRIVATE_KEY[:50]}...")
print(f"   Claim Email: {VAPID_CLAIM_EMAIL}")

# Test 1: Try with pywebpush directly
print("\n2. USING PYWEBPUSH DIRECTLY:")
try:
    import json

    from pywebpush import webpush

    # Create test subscription data
    subscription_info = {
        "endpoint": "https://updates.push.services.mozilla.com/push/test",
        "keys": {
            "p256dh": "BElj4Uh9OjYHQy5w9nv7E-7hKJ8",
            "auth": "myAuthSecret"
        }
    }

    # Try the call
    result = webpush(
        subscription_info=subscription_info,
        data=json.dumps({"title": "Test"}),
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims={"sub": VAPID_CLAIM_EMAIL},
        verbose=False
    )
    print(f"   Result: {result}")
    print(f"   Headers sent: {result.request.headers if hasattr(result, 'request') else 'Unknown'}")
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")

# Test 2: Try manual JWT generation
print("\n3. MANUAL JWT GENERATION:")
try:
    import time

    import jwt
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    # Load private key
    private_key = serialization.load_pem_private_key(
        VAPID_PRIVATE_KEY.encode(),
        password=None,
        backend=default_backend()
    )
    print("   ✓ Private key loaded")

    # Generate JWT
    now = int(time.time())
    claims = {
        "sub": VAPID_CLAIM_EMAIL,
        "aud": "https://fcm.googleapis.com",
        "iat": now,
        "exp": now + 3600
    }

    token = jwt.encode(claims, private_key, algorithm="ES256")
    print(f"   ✓ JWT generated: {token[:50]}...")
    print(f"   ✓ JWT length: {len(token)}")

    # Decode to verify
    decoded = jwt.decode(token, private_key.public_key(), algorithms=["ES256"])
    print(f"   ✓ JWT verified - claims: {decoded}")

except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
