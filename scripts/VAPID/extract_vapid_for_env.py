#!/usr/bin/env python3
"""Extract VAPID keys in .env format."""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

# Load the private key
with open("src/private_key.pem", "rb") as f:
    private_pem_bytes = f.read()

private_key = serialization.load_pem_private_key(private_pem_bytes, password=None, backend=default_backend())

# Get public key
public_key = private_key.public_key()

# Export public key in X962 format (uncompressed point)
public_der = public_key.public_bytes(
    encoding=serialization.Encoding.X962, format=serialization.PublicFormat.UncompressedPoint
)

# Convert to base64url
public_b64url = base64.urlsafe_b64encode(public_der).decode().rstrip("=")

print("=" * 80)
print("VAPID KEYS FOR .env")
print("=" * 80)

print("\nVAPID_PUBLIC_KEY (copy this):")
print(public_b64url)

# Read and escape private key for .env
with open("src/private_key.pem", "r") as f:
    private_pem = f.read()

# In .env format, newlines are represented as \n in the string value
private_escaped = private_pem.replace("\n", "\\n")
print("\nVAPID_PRIVATE_KEY (copy this):")
print(private_escaped)

print("\n" + "=" * 80)
