import os

import requests
from dotenv import load_dotenv

# Load src/.env to get the secret
load_dotenv("src/.env")

PUSH_SERVICE_URL = os.getenv("PUSH_SERVICE_URL", "http://localhost:4000")
SECRET = os.getenv("PUSH_SERVICE_SECRET")


def verify_auth():
    print(f"🔍 Verifying Microservice Auth at {PUSH_SERVICE_URL}...")

    if not SECRET:
        print("❌ CRITICAL: PUSH_SERVICE_SECRET not found in environment!")
        return

    # 1. Test UNAUTHORIZED (No Token)
    try:
        print("   Testing Unauthorized Access...", end=" ")
        resp = requests.get(f"{PUSH_SERVICE_URL}/health")  # Health might be public, check send endpoint
        # The /send endpoint expects POST. Let's try GET /send which might 404 but checking auth middleware usually comes first?
        # Actually simplest check: Try to call /send without header
        resp = requests.post(f"{PUSH_SERVICE_URL}/send", json={})

        if resp.status_code == 401 or resp.status_code == 403:
            print(f"✅ PASS ({resp.status_code})")
        else:
            print(f"❌ FAIL (Got {resp.status_code}, expected 401/403)")
            print(resp.text)

    except Exception as e:
        print(f"❌ FAIL (Connection Error: {e})")

    # 2. Test AUTHORIZED (With Token)
    try:
        print("   Testing Authorized Access...", end=" ")
        # We'll send a dummy payload that fails validation but Passes Auth
        # This proves the token was accepted even if payload is bad.
        headers = {"Authorization": f"Bearer {SECRET}"}
        resp = requests.post(f"{PUSH_SERVICE_URL}/send", json={}, headers=headers)

        # If token is valid, we expect 400 (Bad Request - missing fields) NOT 401
        if resp.status_code != 401 and resp.status_code != 403:
            print(f"✅ PASS (Got {resp.status_code} - Auth accepted)")
        else:
            print(f"❌ FAIL (Got {resp.status_code} - Auth rejected)")
            print(resp.text)

    except Exception as e:
        print(f"❌ FAIL (Connection Error: {e})")


if __name__ == "__main__":
    verify_auth()
