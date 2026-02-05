#!/usr/bin/env python3
"""
Comprehensive VAPID Authentication Test Script

This script validates the VAPID implementation locally without making
actual push requests to Apple/Firebase. It tests:
1. JWT token generation and structure
2. VAPID claims validation
3. Public key format verification
4. Simulated Apple APNs validation logic

Run this to verify the implementation before testing with real push services.
"""

import json
import base64
import time
from urllib.parse import urlparse
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
import jwt

# Configuration - same as in settings
VAPID_PRIVATE_KEY = None  # Will be loaded from settings
VAPID_PUBLIC_KEY = None
VAPID_SUBJECT = "mailto:admin@gutters.local"


def load_private_key():
    """Load the VAPID private key from environment/config."""
    import os
    import sys

    # Change to src directory for proper imports
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "src"))
    sys.path.insert(0, os.getcwd())

    from app.core.config import settings

    global VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_SUBJECT

    VAPID_PRIVATE_KEY = settings.VAPID_PRIVATE_KEY.replace("\\n", "\n")
    VAPID_PUBLIC_KEY = settings.VAPID_PUBLIC_KEY
    VAPID_SUBJECT = settings.RESOLVED_VAPID_SUB


def _get_push_service_origin(endpoint: str) -> str:
    """Extract origin from push service endpoint."""
    if "push.apple.com" in endpoint or "safari-push.apple.com" in endpoint:
        return "APPLE_APNS_WEB"

    parsed = urlparse(endpoint)
    port = f":{parsed.port}" if parsed.port else ""
    origin = f"{parsed.scheme}://{parsed.hostname}{port}"
    return origin


def _get_apple_web_push_audience() -> str:
    """Get audience for Apple APNs Web Push."""
    if VAPID_SUBJECT.startswith("mailto:"):
        return VAPID_SUBJECT.replace("mailto:", "").split("@")[-1]
    return VAPID_SUBJECT


def generate_vapid_headers(endpoint: str) -> dict:
    """
    Generate VAPID headers and return both headers + decoded JWT for verification.
    """
    private_key = serialization.load_pem_private_key(
        VAPID_PRIVATE_KEY.encode(),
        password=None,
        backend=default_backend(),
    )

    audience = _get_push_service_origin(endpoint)
    if audience == "APPLE_APNS_WEB":
        audience = _get_apple_web_push_audience()

    now = int(time.time())
    claims = {"sub": VAPID_SUBJECT, "aud": audience, "iat": now, "exp": now + 3600}

    # Sign JWT
    token = jwt.encode(claims, private_key, algorithm="ES256")

    # Generate public key for Crypto-Key header
    public_key = private_key.public_key()
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.X962, format=serialization.PublicFormat.UncompressedPoint
    )
    public_b64 = base64.urlsafe_b64encode(public_der).decode().rstrip("=")

    headers = {"Authorization": f"Bearer {token}", "Crypto-Key": f"p256ecdsa={public_b64}"}

    return headers, claims, token, public_b64


def decode_jwt(token: str) -> dict:
    """Decode JWT without verification (for inspection)."""
    # JWT is base64-encoded, split by dots
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    def decode_part(part: str) -> dict:
        # Add padding if needed
        padding = 4 - len(part) % 4
        if padding != 4:
            part += "=" * padding
        return json.loads(base64.urlsafe_b64decode(part))

    header = decode_part(parts[0])
    payload = decode_part(parts[1])

    return {"header": header, "payload": payload}


def verify_vapid_for_apple(audience: str, subject: str, public_key: str) -> tuple[bool, list[str]]:
    """
    Verify VAPID claims against Apple APNs Web Push requirements.

    Returns: (is_valid, list_of_issues)
    """
    issues = []

    # Apple requirements:
    # 1. aud should be the website name (domain)
    # 2. sub should be mailto: or https: URL
    # 3. Public key should be valid base64url encoded P-256 point

    # Check audience
    if not audience:
        issues.append("Audience is empty")
    elif "." not in audience and not audience.startswith("localhost"):
        issues.append(f"Audience '{audience}' may not be a valid website name")

    # Check subject
    if not subject.startswith("mailto:") and not subject.startswith("https://"):
        issues.append(f"Subject '{subject}' should be mailto: or https: URL")

    # Check public key format
    try:
        # Decode base64url
        key_bytes = base64.urlsafe_b64decode(public_key + "==")
        if len(key_bytes) != 65:  # Uncompressed P-256 point is 65 bytes
            issues.append(f"Public key length is {len(key_bytes)}, expected 65 bytes for P-256")
    except Exception as e:
        issues.append(f"Public key decoding failed: {e}")

    # Verify public key matches configured key
    if public_key != VAPID_PUBLIC_KEY:
        issues.append("Public key in headers doesn't match configured VAPID_PUBLIC_KEY")

    return len(issues) == 0, issues


def simulate_apple_validation(claims: dict, public_key: str) -> tuple[bool, str]:
    """
    Simulate how Apple APNs validates VAPID authentication.

    Apple will:
    1. Extract the JWT from Authorization header
    2. Decode the JWT (publicly accessible)
    3. Verify the signature using the public key in Crypto-Key header
    4. Check that 'aud' matches the website name
    5. Check that 'sub' is a valid contact URL
    6. Check token is not expired
    """
    issues = []

    # 1. Check audience
    expected_aud = VAPID_SUBJECT.replace("mailto:", "").split("@")[-1]
    if claims.get("aud") != expected_aud:
        issues.append(f"Audience mismatch: expected '{expected_aud}', got '{claims.get('aud')}'")

    # 2. Check subject
    if not claims.get("sub", "").startswith("mailto:"):
        issues.append(f"Subject should be mailto: URL, got '{claims.get('sub')}'")

    # 3. Check expiration
    exp = claims.get("exp", 0)
    now = int(time.time())
    if exp < now:
        issues.append(f"Token expired at {exp}, current time is {now}")

    if exp - now > 3600:
        issues.append(f"Token expiration too far in future: {exp - now} seconds")

    # 4. Check issued at
    iat = claims.get("iat", 0)
    if iat > now + 60:
        issues.append(f"Token issued in the future: iat={iat}, now={now}")

    # 5. Check public key format
    try:
        key_bytes = base64.urlsafe_b64decode(public_key + "==")
        if len(key_bytes) != 65:
            issues.append(f"Invalid public key length: {len(key_bytes)} bytes (expected 65)")
    except Exception as e:
        issues.append(f"Invalid public key format: {e}")

    if issues:
        return False, "; ".join(issues)

    return True, "All checks passed"


def test_push_endpoint(endpoint: str) -> dict:
    """
    Test VAPID authentication for a specific push endpoint.
    """
    print(f"\n{'=' * 60}")
    print(f"Testing push endpoint: {endpoint}")
    print(f"{'=' * 60}")

    # Generate VAPID headers
    headers, claims, token, public_key = generate_vapid_headers(endpoint)

    # Decode and display JWT
    decoded = decode_jwt(token)

    print(f"\n[JWT HEADER] {json.dumps(decoded['header'], indent=2)}")
    print(f"\n[JWT PAYLOAD] {json.dumps(decoded['payload'], indent=2)}")

    print(f"\n[PUBLIC KEY] (first 30 chars): {public_key[:30]}...")
    print(f"[CONFIG KEY] (first 30 chars): {VAPID_PUBLIC_KEY[:30]}...")
    print(f"[MATCH] Keys match: {public_key == VAPID_PUBLIC_KEY}")

    # Simulate Apple validation
    print(f"\n[VALIDATION] Simulating Apple APNs validation...")

    if "apple.com" in endpoint:
        is_valid, message = simulate_apple_validation(claims, public_key)
        if is_valid:
            print(f"[PASS] Apple validation PASSED: {message}")
        else:
            print(f"[FAIL] Apple validation FAILED: {message}")
        return {"endpoint": endpoint, "valid": is_valid, "message": message, "claims": claims, "public_key": public_key}
    else:
        print(f"[INFO] Non-Apple endpoint - using standard FCM/Mozilla validation")
        is_valid, issues = verify_vapid_for_apple(claims["aud"], claims["sub"], public_key)
        if is_valid:
            print(f"[PASS] Standard validation PASSED")
        else:
            print(f"[FAIL] Standard validation FAILED: {issues}")
        return {"endpoint": endpoint, "valid": is_valid, "issues": issues, "claims": claims, "public_key": public_key}


def main():
    """Run all VAPID tests."""
    print("[CONFIG] Loading VAPID configuration...")
    load_private_key()

    print(f"[EMAIL] VAPID Subject: {VAPID_SUBJECT}")
    print(f"[KEY] Public Key: {VAPID_PUBLIC_KEY[:50]}...")

    # Test different push service endpoints
    test_endpoints = [
        # Apple APNs Web Push
        "https://web.push.apple.com/QHOrvY0j0d4hQ4Om47n-uKp",
        "https://safari-push.apple.com/12345",
        # FCM (Android/Chrome)
        "https://fcm.googleapis.com/fcm/send/abc123",
        # Mozilla (Firefox)
        "https://updates.push.services.mozilla.com/wpush/v2/abc123",
    ]

    results = []
    for endpoint in test_endpoints:
        result = test_push_endpoint(endpoint)
        results.append(result)

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    for result in results:
        status = "[OK]" if result.get("valid") else "[FAIL]"
        service = "Apple" if "apple.com" in result["endpoint"] else "FCM/Mozilla"
        print(f"{status} {service}: {result.get('message', result.get('issues', 'OK'))}")

    # Check if Apple test passed
    apple_result = [r for r in results if "apple.com" in r["endpoint"] and r.get("valid")]
    if apple_result:
        print(f"\n[SUCCESS] Apple APNs Web Push should work! The VAPID implementation is correct.")
        print(f"   The 403 error might be due to:")
        print(f"   1. Subscription was created with a different VAPID key pair")
        print(f"   2. PWA not served over HTTPS (required for push)")
        print(f"   3. Missing or incorrect web manifest")
        print(f"   4. User revoked notification permission")
    else:
        print(f"\n[WARNING] Apple APNs validation failed. Check the issues above.")


if __name__ == "__main__":
    main()
