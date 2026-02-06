import os
import sys

# Add project root to sys.path explicitly just in case
sys.path.append(os.getcwd())

print("1. Importing Base...")

print("2. Importing User...")
try:

    print("   User imported successfully.")
except Exception as e:
    print(f"   User import FAILED: {e}")

print("3. Importing PlayerStats...")
try:

    print("   PlayerStats imported successfully.")
except Exception as e:
    print(f"   PlayerStats import FAILED: {e}")

print("4. Configuring Mappers...")
from sqlalchemy.orm import configure_mappers

try:
    configure_mappers()
    print("   Mappers configured.")
except Exception as e:
    print(f"   Mapper configuration FAILED: {e}")
