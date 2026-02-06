#!/usr/bin/env python3
"""
Test actual push send with debugging to see EXACTLY what's being sent to Apple.
"""

import json
import os
import sys

# Change to src directory for proper imports
os.chdir(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.getcwd())

# Monkey-patch requests to see EXACTLY what's being sent
import requests

original_post = requests.post

def debug_post(url, **kwargs):
    print("\n" + "="*60)
    print("ACTUAL REQUEST TO APPLE:")
    print("="*60)
    print(f"URL: {url}")
    print("\nHeaders:")
    for k, v in kwargs.get('headers', {}).items():
        print(f"  {k}: {v[:100]}..." if len(str(v)) > 100 else f"  {k}: {v}")
    print(f"\nBody: {kwargs.get('data', 'None')[:200]}...")
    print("="*60 + "\n")

    response = original_post(url, **kwargs)

    print("\n" + "="*60)
    print("RESPONSE FROM APPLE:")
    print("="*60)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body: {response.text}")
    print("="*60 + "\n")

    return response

requests.post = debug_post

# Now import and test
from pywebpush import webpush

from app.core.config import settings
from app.modules.infrastructure.push.service import generate_vapid_headers

# Test endpoint (Apple)
endpoint = "https://web.push.apple.com/QGakvLVPQzw75IOb6lXCdQZX9IhJIAo08vVcnLGaUNjL3B8_TCQY8Sj3ATBNl-9gIXm9-3BDqUzX00nwYK1X8HKjpRNcHKVVhg2Jqjb"

# Generate VAPID headers
print("Generating VAPID headers...")
vapid_headers = generate_vapid_headers(
    settings.VAPID_PRIVATE_KEY.replace("\\n", "\n"),
    settings.RESOLVED_VAPID_SUB,
    endpoint
)

print("\nGenerated headers:")
print(f"  Authorization: {vapid_headers['Authorization'][:80]}...")
print(f"  Crypto-Key: {vapid_headers['Crypto-Key'][:80]}...")

# Test subscription (use fake keys for this test)
subscription = {
    "endpoint": endpoint,
    "keys": {
        "p256dh": "BKPJQFEn_zGiRTOF7qw5LqTZm0tVQwSl-SH72KdYQCE",
        "auth": "abc123"
    }
}

payload = json.dumps({"title": "Test", "body": "Testing", "url": "/"})

print("\nAttempting to send push notification...")
print("Using pywebpush with headers parameter\n")

try:
    webpush(
        subscription_info=subscription,
        data=payload,
        headers=vapid_headers
    )
    print("\n✅ SUCCESS!")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
