#!/usr/bin/env python3
"""
GUTTERS Redis Connection Test

Diagnoses Redis connection issues and verifies all functionality.

Usage:
    python src/scripts/test_redis_connection.py
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))


async def test_connection():
    """Test Redis connection and functionality."""
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        
        print("[*] Testing Redis Connection...")
        print("=" * 60)
        
        # Show configuration (hide password)
        password_display = settings.REDIS_PASSWORD[:3] + "*" * (len(settings.REDIS_PASSWORD) - 3) if settings.REDIS_PASSWORD else "NOT SET"
        
        print("Configuration:")
        print(f"  Host: {settings.REDIS_CACHE_HOST}")
        print(f"  Port: {settings.REDIS_CACHE_PORT}")
        print(f"  Password: {password_display}")
        print(f"  URL: {settings.REDIS_CACHE_URL[:50]}...")
        print("=" * 60)
        
        # Test 1: Basic Connection
        print("\n[1/5] Testing basic connection...")
        
        # Try connection without SSL first (Redis Cloud free tier)
        # If SSL is required, will fall back to SSL connection
        try:
            client = redis.Redis(
                host=settings.REDIS_CACHE_HOST,
                port=settings.REDIS_CACHE_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
            )
            pong = await client.ping()
            print("  [OK] Connected without SSL")
        except Exception as e:
            print(f"  [INFO] Non-SSL failed ({e}), trying with SSL...")
            client = redis.Redis(
                host=settings.REDIS_CACHE_HOST,
                port=settings.REDIS_CACHE_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                ssl=True,
                ssl_cert_reqs="none",
            )
            pong = await client.ping()
            print("  [OK] Connected with SSL")

        if pong:
            print("  [OK] PING successful - Redis is responding")
        else:
            print("  [FAIL] PING failed")
            return 1
        
        # Test 2: SET/GET operations
        print("\n[2/5] Testing SET/GET operations...")
        test_key = "gutters:test:connection"
        test_value = "hello_gutters_" + str(asyncio.get_event_loop().time())
        
        await client.set(test_key, test_value, ex=30)  # 30 second expiry
        retrieved = await client.get(test_key)
        
        if retrieved == test_value:
            print(f"  [OK] SET/GET working - value matched")
        else:
            print(f"  [FAIL] SET/GET mismatch: expected '{test_value}', got '{retrieved}'")
            return 1
        
        # Test 3: DELETE operation
        print("\n[3/5] Testing DELETE operation...")
        await client.delete(test_key)
        deleted_check = await client.get(test_key)
        
        if deleted_check is None:
            print("  [OK] DELETE working - key removed")
        else:
            print("  [FAIL] DELETE failed - key still exists")
            return 1
        
        # Test 4: JSON operations (for complex data)
        print("\n[4/5] Testing JSON storage...")
        import json
        
        test_json = {
            "module": "astrology",
            "planets": ["Sun", "Moon", "Mercury"],
            "calculated": True
        }
        
        json_key = "gutters:test:json"
        await client.set(json_key, json.dumps(test_json), ex=30)
        retrieved_json = await client.get(json_key)
        parsed = json.loads(retrieved_json)
        
        if parsed == test_json:
            print("  [OK] JSON storage working")
        else:
            print("  [FAIL] JSON storage mismatch")
            return 1
        
        await client.delete(json_key)
        
        # Test 5: Pub/Sub (basic check)
        print("\n[5/5] Testing Pub/Sub...")
        pubsub = client.pubsub()
        await pubsub.subscribe("gutters:test:channel")
        
        # Publish a message
        await client.publish("gutters:test:channel", "test_message")
        
        # Give time for message to arrive
        message = None
        for _ in range(10):
            msg = await pubsub.get_message(timeout=0.1)
            if msg and msg.get("type") == "message":
                message = msg
                break
        
        await pubsub.unsubscribe("gutters:test:channel")
        await pubsub.close()
        
        if message:
            print(f"  [OK] Pub/Sub working - received message")
        else:
            print("  [WARN] Pub/Sub - no message received (may need more time)")
        
        await client.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("[OK] Redis connection test passed!")
        print("=" * 60)
        print("\nRedis is ready for:")
        print("  - Event Bus (pub/sub)")
        print("  - Active Memory (caching)")
        print("  - Rate Limiting")
        print("  - Task Queue (arq)")
        
        return 0
        
    except ImportError as e:
        print("\n" + "=" * 60)
        print("[FAIL] Missing dependency")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nInstall required packages:")
        print("  pip install redis")
        return 1
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("[FAIL] Connection failed")
        print("=" * 60)
        print(f"Error: {type(e).__name__}: {e}")
        print("\nCommon causes:")
        print("  1. Redis server not running")
        print("  2. Incorrect credentials in .env")
        print("  3. Firewall blocking connection")
        print("  4. Wrong host/port")
        print("\nFor Redis Cloud:")
        print("  - Check your Redis Cloud dashboard")
        print("  - Verify host, port, and password")
        print("  - Ensure database is active")
        print("\nVerify .env settings:")
        print("  REDIS_CACHE_HOST=your-redis-host.cloud.redislabs.com")
        print("  REDIS_CACHE_PORT=12345")
        print("  REDIS_PASSWORD=your-password")
        return 1


def main():
    """Main entry point."""
    exit_code = asyncio.run(test_connection())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
