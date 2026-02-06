#!/usr/bin/env python3
"""
Generate VAPID keys in base64url format (like Node.js web-push library uses).
"""

import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid01

# Generate keys
vapid = Vapid01()
vapid.generate_keys()

# Get keys in different formats
private_key_bytes = vapid.private_key.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption()
)

public_key_bytes = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Convert to base64url
private_b64 = base64.urlsafe_b64encode(private_key_bytes).decode().rstrip('=')
public_b64 = base64.urlsafe_b64encode(public_key_bytes).decode().rstrip('=')

print("Copy these to your .env:")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print(f"VAPID_PRIVATE_KEY={private_b64}")
print("VAPID_CLAIM_EMAIL=mailto:admin@4shdt3z4-5173.aue.devtunnels.ms")
