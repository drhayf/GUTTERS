import sys
import os

# Add project root to sys.path explicitly just in case
sys.path.append(os.getcwd())

print("1. Importing Base...")
from src.app.core.db.database import Base

print("2. Importing User...")
try:
    from src.app.models.user import User

    print("   User imported successfully.")
except Exception as e:
    print(f"   User import FAILED: {e}")

print("3. Importing PlayerStats...")
try:
    from src.app.models.progression import PlayerStats

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
