#!/usr/bin/env python3
"""Diagnose exact key format and loading issues."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / "src" / ".env"
load_dotenv(env_path)

private_key_raw = os.getenv("VAPID_PRIVATE_KEY", "")
public_key = os.getenv("VAPID_PUBLIC_KEY", "")
claim_email = os.getenv("VAPID_CLAIM_EMAIL", "")

print("=" * 80)
print("VAPID KEY FORMAT DIAGNOSTIC")
print("=" * 80)

print("\n1. RAW PRIVATE KEY FROM ENV (first 100 chars):")
print(repr(private_key_raw[:100]))

print("\n2. PRIVATE KEY LENGTH:", len(private_key_raw))

print("\n3. CONTAINS LITERAL \\n (backslash + n)?")
print("   Count of '\\\\n':", private_key_raw.count("\\n"))

print("\n4. PRIVATE KEY AFTER REPLACE (first 100 chars):")
private_key_processed = private_key_raw.replace("\\n", "\n")
print(repr(private_key_processed[:100]))

print("\n5. STARTS WITH '-----BEGIN'?", private_key_processed.startswith("-----BEGIN"))
print("6. ENDS WITH '-----END'?", private_key_processed.rstrip().endswith("-----"))

print("\n7. CHECKING PYWEBPUSH HANDLING:")
try:
    from pywebpush import webpush
    from py_vapid import Vapid02

    # Try to load with py_vapid
    try:
        vapid = Vapid02()
        vapid.from_pem(private_key_processed)
        print("   ✓ py_vapid.from_pem() succeeded")
        print("   ✓ Private key property:", "SET" if vapid.private_key else "NULL")
    except Exception as e:
        print(f"   ✗ py_vapid.from_pem() failed: {e}")

    # Try to load with cryptography library
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    try:
        key = serialization.load_pem_private_key(
            private_key_processed.encode(), password=None, backend=default_backend()
        )
        print("   ✓ cryptography.load_pem_private_key() succeeded")
    except Exception as e:
        print(f"   ✗ cryptography.load_pem_private_key() failed: {e}")

except Exception as e:
    print(f"   Error during import: {e}")

print("\n8. PUBLIC KEY (first 50 chars):", public_key[:50])
print("   Length:", len(public_key))

print("\n9. CLAIM EMAIL:", claim_email)

print("\n" + "=" * 80)
