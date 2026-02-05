from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64


def generate_vapid_keys_raw():
    # 1. Generate Private Key (EC P-256)
    private_key = ec.generate_private_key(ec.SECP256R1())

    # 2. Get Private Scalar (32 bytes)
    private_val = private_key.private_numbers().private_value
    private_bytes = private_val.to_bytes(32, byteorder="big")
    private_b64 = base64.urlsafe_b64encode(private_bytes).decode("utf-8").rstrip("=")

    # 3. Derive Public Key (Uncompressed Point)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    x = public_numbers.x.to_bytes(32, byteorder="big")
    y = public_numbers.y.to_bytes(32, byteorder="big")
    raw_public = b"\x04" + x + y
    public_b64 = base64.urlsafe_b64encode(raw_public).decode("utf-8").rstrip("=")

    print("--- NEW RAW KEYS ---")
    print(f"VAPID_PUBLIC_KEY={public_b64}")
    print(f"VAPID_PRIVATE_KEY={private_b64}")
    print("--------------------")


if __name__ == "__main__":
    generate_vapid_keys_raw()
