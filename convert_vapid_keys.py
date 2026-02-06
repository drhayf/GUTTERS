import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_private_key,
)

# Read private key PEM
with open("private_key.pem", "rb") as f:
    private_key = load_pem_private_key(f.read(), None, default_backend())

# Extract raw EC private key number (32 bytes for P-256)
# This is what pywebpush expects - just the raw 32-byte secret

private_numbers = private_key.private_numbers()
private_value_bytes = private_numbers.private_value.to_bytes(32, byteorder="big")

# Convert to base64url
private_key_b64 = base64.urlsafe_b64encode(private_value_bytes).decode().rstrip("=")

# Extract public key in X962 uncompressed format
public_key_raw = private_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)

# Convert to base64url (VAPID format)
public_key_b64 = base64.urlsafe_b64encode(public_key_raw).decode().rstrip("=")

print("# For pywebpush (base64url-encoded raw values):")
print(f'VAPID_PRIVATE_KEY="{private_key_b64}"')
print(f'VAPID_PUBLIC_KEY="{public_key_b64}"')
print()
print(f"Private key length: {len(private_key_b64)} chars (should be 43)")
print(f"Public key length: {len(public_key_b64)} chars (should be 87)")
