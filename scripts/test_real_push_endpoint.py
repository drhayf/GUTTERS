#!/usr/bin/env python3
"""
Test VAPID with REAL app endpoint
Calls the ACTUAL app /api/v1/push/test endpoint to see real BadJwtToken errors
"""

import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import json

import requests

API_URL = "http://localhost:8000"
TEST_USER = "testeruser"
TEST_PASSWORD = "Str1ngT3st!"

print("=" * 70)
print("REAL APP VAPID TEST")
print("Testing against ACTUAL server endpoint")
print("=" * 70)
print()

# Step 1: Get access token
print("STEP 1: Logging in to get access token")
print("-" * 70)

try:
    # Using form data for OAuth2PasswordRequestForm
    login_response = requests.post(
        f"{API_URL}/login", data={"username": TEST_USER, "password": TEST_PASSWORD}, timeout=5
    )

    if login_response.status_code != 200:
        print(f"FAILED: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        sys.exit(1)

    token_data = login_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        print(f"No access token in response: {token_data}")
        sys.exit(1)

    print("OK - Login successful")
    print(f"Token: {access_token[:30]}...\n")

except requests.exceptions.ConnectionError:
    print(f"FAILED - Cannot connect to {API_URL}")
    print("Is the app running? Try: uv run uvicorn src.app.main:app --reload")
    sys.exit(1)
except Exception as e:
    print(f"FAILED - Login error: {e}")
    sys.exit(1)

# Step 2: Call test endpoint
print("STEP 2: Calling /api/v1/push/test endpoint")
print("-" * 70)

try:
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    test_response = requests.post(f"{API_URL}/api/v1/push/test", headers=headers, timeout=10)

    print(f"Status code: {test_response.status_code}")

    if test_response.status_code == 200:
        results = test_response.json()
        print("OK - Test endpoint responded")
        print(f"\nResults: {json.dumps(results, indent=2)}")

        if "results" in results:
            res = results["results"]
            print("\nSummary:")
            print(f"  Success: {res.get('success', 0)}")
            print(f"  Failed: {res.get('failed', 0)}")
            print(f"  Expired: {res.get('expired', 0)}")

            if res.get("failed", 0) > 0:
                print(f"\nFAILED - {res['failed']} notifications FAILED")
                print("This is where BadJwtToken errors appear!")
            elif res.get("success", 0) > 0:
                print(f"\nSUCCESS - {res['success']} notifications sent successfully!")
                print("VAPID keys are working!")
            else:
                print("\nNo subscriptions to test with")
    else:
        print(f"FAILED - Status: {test_response.status_code}")
        print(f"Response: {test_response.text}")

except Exception as e:
    print(f"FAILED - Error: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
