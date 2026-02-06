#!/usr/bin/env python3
"""
Inspect the actual subscription data in the database.
"""

import asyncio
import os
import sys

# Change to src directory
os.chdir(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.getcwd())

from sqlalchemy import select

from app.core.db.database import local_session
from app.models.push import PushSubscription


async def main():
    print("=" * 60)
    print("SUBSCRIPTION DATA INSPECTION")
    print("=" * 60)

    async with local_session() as db:
        stmt = select(PushSubscription).where(PushSubscription.user_id == 78)
        result = await db.execute(stmt)
        subs = result.scalars().all()

        if not subs:
            print("\n❌ No subscriptions found for user 78")
            return

        for i, sub in enumerate(subs):
            print(f"\n[SUBSCRIPTION {i + 1}]")
            print("-" * 60)
            print(f"Endpoint: {sub.endpoint}")
            print(f"P256dh length: {len(sub.p256dh)} chars")
            print(f"Auth length: {len(sub.auth)} chars")
            print(f"P256dh (first 40): {sub.p256dh[:40]}...")
            print(f"Auth (first 20): {sub.auth[:20]}...")
            print(f"\nEndpoint type: {'Apple APNs' if 'apple.com' in sub.endpoint else 'Other'}")

            # Validate base64url format
            try:
                import base64

                base64.urlsafe_b64decode(sub.p256dh + "==")
                print("✅ P256dh is valid base64url")
            except Exception:
                print("❌ P256dh is NOT valid base64url")

            try:
                base64.urlsafe_b64decode(sub.auth + "==")
                print("✅ Auth is valid base64url")
            except Exception:
                print(" Auth is NOT valid base64url")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
