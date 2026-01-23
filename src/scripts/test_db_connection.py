#!/usr/bin/env python3
"""
GUTTERS Database Connection Test

Diagnoses database connection issues by testing connectivity
and verifying configuration.

Usage:
    python src/scripts/test_db_connection.py
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))


async def test_connection():
    """Test database connection and list tables."""
    try:
        import asyncpg
        from app.core.config import settings
        
        print("[*] Testing Database Connection...")
        print("=" * 60)
        
        # Show configuration (hide password)
        password_display = settings.POSTGRES_PASSWORD[:3] + "*" * (len(settings.POSTGRES_PASSWORD) - 3) if settings.POSTGRES_PASSWORD else "NOT SET"
        
        print("Configuration:")
        print(f"  Host: {settings.POSTGRES_SERVER}")
        print(f"  Port: {settings.POSTGRES_PORT}")
        print(f"  User: {settings.POSTGRES_USER}")
        print(f"  Database: {settings.POSTGRES_DB}")
        print(f"  Password: {password_display}")
        print(f"  Connection URL: {settings.POSTGRES_ASYNC_PREFIX}{settings.POSTGRES_USER}@{settings.POSTGRES_SERVER}...")
        print("=" * 60)
        
        # Attempt connection
        print("\nAttempting connection...")
        
        conn = await asyncpg.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        
        print("[OK] Connected successfully!")
        
        # List tables
        print("\nQuerying tables...")
        tables = await conn.fetch(
            """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        
        if tables:
            print(f"\nTables found ({len(tables)}):")
            for table in tables:
                print(f"  - {table['tablename']}")
        else:
            print("\n[WARNING] No tables found in database")
            print("Run migrations to create tables:")
            print("  cd src && python -m alembic upgrade head")
        
        await conn.close()
        
        print("\n" + "=" * 60)
        print("[OK] Database connection test passed!")
        print("=" * 60)
        return 0
        
    except ImportError as e:
        print("\n" + "=" * 60)
        print("[FAIL] Missing dependency")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nInstall required packages:")
        print("  pip install asyncpg")
        return 1
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("[FAIL] Connection failed")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nCommon causes:")
        print("  1. PostgreSQL not running")
        print("  2. Incorrect credentials in .env file")
        print("  3. Firewall blocking connection")
        print("  4. Wrong host/port")
        print("\nFor Supabase:")
        print("  - Check Project Settings > Database")
        print("  - Use 'Connection Pooling' settings (port 6543)")
        print("  - Verify password is correct")
        print("  - Host format: aws-X-region.pooler.supabase.com")
        print("\nVerify .env settings:")
        print("  POSTGRES_SERVER=your-host.supabase.com")
        print("  POSTGRES_PORT=6543")
        print("  POSTGRES_USER=postgres.xxxxx")
        print("  POSTGRES_PASSWORD=your-password")
        print("  POSTGRES_DB=postgres")
        return 1


def main():
    """Main entry point."""
    exit_code = asyncio.run(test_connection())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
