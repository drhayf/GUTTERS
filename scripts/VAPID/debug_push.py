import asyncio
import json
import logging

# Add project root to sys.path
import os
import sys
import traceback

from pywebpush import WebPushException, webpush
from sqlalchemy import func, select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app.core.config import settings
from src.app.core.db.database import local_session
from src.app.models.push import PushSubscription

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PushDebugger")


async def run_smoke_test():
    logger.info("--- 1. CHECKING VAPID KEYS ---")

    public_key = settings.VAPID_PUBLIC_KEY
    private_key = settings.VAPID_PRIVATE_KEY
    claim_sub = settings.VAPID_CLAIMS_SUB or "mailto:admin@example.com"

    if not public_key:
        logger.error("MISSING VAPID_PUBLIC_KEY in settings!")
    else:
        logger.info(f"VAPID_PUBLIC_KEY found: {public_key[:15]}...")

    if not private_key:
        logger.error("MISSING VAPID_PRIVATE_KEY in settings!")
    else:
        # Handle escaped newlines just in case, similar to service
        private_key = private_key.replace("\\n", "\n")
        logger.info(f"VAPID_PRIVATE_KEY loaded. First 20 chars: {repr(private_key[:20])}")
        logger.info(f"VAPID_PRIVATE_KEY total length: {len(private_key)}")

    if not public_key or not private_key:
        logger.error("ABORTING: Cannot test without VAPID keys.")
        return

    logger.info("--- 2. CHECKING SUBSCRIPTIONS ---")

    subscription_to_test = None

    async with local_session() as db:
        # Check total count
        count = await db.scalar(select(func.count(PushSubscription.id)))
        logger.info(f"Total Push Subscriptions in DB: {count}")

        if count == 0:
            logger.error("CRITICAL: No subscriptions found in DB. Frontend failed to register.")
            return

        # Fetch one to test
        stmt = select(PushSubscription).limit(1)
        result = await db.execute(stmt)
        subscription_to_test = result.scalar_one_or_none()

    if not subscription_to_test:
        logger.error("Failed to retrieve subscription object.")
        return

    logger.info(f"Testing Subscription ID: {subscription_to_test.id}")
    logger.info(f"Endpoint: {subscription_to_test.endpoint[:50]}...")
    logger.info(f"User Agent: {subscription_to_test.user_agent}")

    logger.info("--- 3. FORCE SENDING NOTIFICATION ---")

    payload = {
        "title": "Smoke Test",
        "body": "This is a direct test from the backend script.",
        "url": "/debug",
        "icon": "/icons/icon-192x192.png",
    }

    try:
        logger.info("Attempting webpush call...")
        response = webpush(
            subscription_info={
                "endpoint": subscription_to_test.endpoint,
                "keys": {"p256dh": subscription_to_test.p256dh, "auth": subscription_to_test.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=private_key,
            vapid_claims={"sub": claim_sub},
            timeout=10,
        )

        # If webpush returns, it's usually successful (errors raise Exceptions)
        logger.info(f"SUCCESS! WebPush returned: {response}")
        # Some libraries return a response object, lets try to print status if available
        if hasattr(response, "status_code"):
            logger.info(f"Status Code: {response.status_code}")
        if hasattr(response, "text"):
            logger.info(f"Response Body: {response.text}")

    except WebPushException as ex:
        logger.error("WebPushException CAUGHT!")
        logger.error(f"Message: {ex}")
        if ex.response:
            logger.error(f"Remote Response Status: {ex.response.status_code}")
            logger.error(f"Remote Response Content: {ex.response.content}")

    except Exception:
        logger.error("General Exception CAUGHT!")
        logger.error(traceback.format_exc())

    logger.info("--- SMOKE TEST COMPLETE ---")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_smoke_test())
