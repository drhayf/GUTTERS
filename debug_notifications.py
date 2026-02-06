import asyncio
import logging
import sys

from sqlalchemy import func, select

from src.app.core.config import settings
from src.app.core.db.database import local_session
from src.app.models.push import PushSubscription
from src.app.models.user_profile import UserProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def diagnose():
    print("--- DIAGNOSTIC START ---")

    # 1. Check VAPID Keys
    print(f"VAPID_PUBLIC_KEY Configured: {bool(settings.VAPID_PUBLIC_KEY)}")
    print(f"VAPID_PRIVATE_KEY Configured: {bool(settings.VAPID_PRIVATE_KEY)}")
    if settings.VAPID_PUBLIC_KEY:
        print(f"VAPID_PUBLIC_KEY (First 10): {settings.VAPID_PUBLIC_KEY[:10]}...")

    # 2. Check Subscriptions
    async with local_session() as db:
        stmt = select(func.count(PushSubscription.id))
        result = await db.execute(stmt)
        count = result.scalar()
        print(f"Total PushSubscription records: {count}")

        if count > 0:
            stmt_sub = select(PushSubscription).limit(1)
            result_sub = await db.execute(stmt_sub)
            sub = result_sub.scalar_one()
            print(f"Sample Subscription Endpoint: {sub.endpoint[:30]}...")
            print(f"Sample Subscription UserID: {sub.user_id}")

        # 3. Check UserProfile
        stmt_profile = select(UserProfile).limit(1)
        result_profile = await db.execute(stmt_profile)
        profile = result_profile.scalar_one_or_none()
        if profile:
            print(f"Sample UserProfile Data: {profile.data}")
        else:
            print("No UserProfile found.")

    print("--- DIAGNOSTIC END ---")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(diagnose())
