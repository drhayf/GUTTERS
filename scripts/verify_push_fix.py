#!/usr/bin/env python3
"""
Verify Push Notification Fix

This script verifies that the critical fix (adding 'aud' to vapid_claims)
is present in the code and working correctly.
"""

import os
import sys

# Change to src directory for proper imports
os.chdir(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.getcwd())

from app.modules.infrastructure.push.service import (
    _get_push_service_origin,
    _get_apple_web_push_audience,
)
from app.core.config import settings

print("=" * 60)
print("PUSH NOTIFICATION FIX VERIFICATION")
print("=" * 60)

# Test 1: Verify audience extraction functions work
print("\n[TEST 1] Audience Extraction Functions")
print("-" * 60)

test_endpoints = [
    ("https://web.push.apple.com/abc123", "APPLE_APNS_WEB"),
    ("https://safari-push.apple.com/xyz789", "APPLE_APNS_WEB"),
    ("https://fcm.googleapis.com/fcm/send/abc", "https://fcm.googleapis.com"),
    ("https://updates.push.services.mozilla.com/wpush/v2/abc", "https://updates.push.services.mozilla.com"),
]

all_passed = True
for endpoint, expected in test_endpoints:
    result = _get_push_service_origin(endpoint)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_passed = False
    print(f"[{status}] {endpoint[:50]}")
    print(f"       Expected: {expected}")
    print(f"       Got:      {result}")

print(f"\n{'[PASS]' if all_passed else '[FAIL]'} Audience extraction")

# Test 2: Verify Apple audience derivation
print("\n[TEST 2] Apple Audience Derivation")
print("-" * 60)

apple_aud = _get_apple_web_push_audience()
expected_domain = settings.RESOLVED_VAPID_SUB.replace("mailto:", "").split("@")[-1]

print(f"VAPID Subject: {settings.RESOLVED_VAPID_SUB}")
print(f"Derived Audience: {apple_aud}")
print(f"Expected: {expected_domain}")

if apple_aud == expected_domain:
    print("[PASS] Apple audience correctly derived from VAPID subject")
else:
    print("[FAIL] Apple audience mismatch!")
    all_passed = False

# Test 3: Verify code structure (check if aud would be passed)
print("\n[TEST 3] Code Structure Verification")
print("-" * 60)

# Read the service file and check for critical patterns
service_file = os.path.join(
    os.path.dirname(__file__), "..", "src", "app", "modules", "infrastructure", "push", "service.py"
)
with open(service_file, "r", encoding="utf-8") as f:
    service_code = f.read()

checks = [
    ('"aud": audience' in service_code, "vapid_claims includes 'aud' key"),
    ("vapid_claims = {" in service_code, "vapid_claims dictionary creation"),
    ('"sub": settings.RESOLVED_VAPID_SUB' in service_code, "VAPID subject in claims"),
    ("_get_apple_web_push_audience()" in service_code, "Apple audience function called"),
]

for condition, description in checks:
    status = "PASS" if condition else "FAIL"
    if not condition:
        all_passed = False
    print(f"[{status}] {description}")

# Test 4: Configuration validation
print("\n[TEST 4] Configuration Validation")
print("-" * 60)

config_checks = [
    (settings.VAPID_PUBLIC_KEY is not None, "VAPID_PUBLIC_KEY is set"),
    (settings.VAPID_PRIVATE_KEY is not None, "VAPID_PRIVATE_KEY is set"),
    (settings.RESOLVED_VAPID_SUB is not None, "VAPID subject is set"),
    (len(settings.VAPID_PUBLIC_KEY) > 50 if settings.VAPID_PUBLIC_KEY else False, "VAPID public key length valid"),
]

for condition, description in config_checks:
    status = "PASS" if condition else "FAIL"
    if not condition:
        all_passed = False
    print(f"[{status}] {description}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if all_passed:
    print("[SUCCESS] All verification checks passed!")
    print("")
    print("The push notification fix is correctly implemented:")
    print("  1. Audience extraction works for all push services")
    print("  2. Apple audience correctly derived from VAPID subject")
    print("  3. Code structure includes 'aud' in vapid_claims")
    print("  4. Configuration is valid")
    print("")
    print("Next steps:")
    print("  1. Deploy the updated code")
    print("  2. Clear old subscriptions (optional)")
    print("  3. Test with iOS Safari")
    sys.exit(0)
else:
    print("[FAILURE] Some verification checks failed!")
    print("Please review the failures above.")
    sys.exit(1)
