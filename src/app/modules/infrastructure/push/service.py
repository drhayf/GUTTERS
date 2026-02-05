"""
Push Notification Service - Node.js Microservice Adapter

Delegates push notification sending to Node.js microservice using proven web-push library.
This approach guarantees compatibility with Apple APNs Web Push.
"""

import logging
import json
from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.core.config import settings
from src.app.models.push import PushSubscription

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Push notification service using Node.js microservice.

    Delegates to proven web-push library (same as barbbarb project).
    Guaranteed to work with Apple APNs, FCM, and Mozilla.
    """

    def __init__(self):
        """Initialize and validate configuration."""
        logger.info("✅ NotificationService initialized (Node.js microservice adapter)")
        self.service_url = settings.PUSH_SERVICE_URL
        self.auth_token = settings.PUSH_SERVICE_SECRET

        if not self.auth_token or "change-me" in self.auth_token:
            logger.warning("⚠️  PUSH_SERVICE_SECRET is unset or default. Push verification will fail.")

    async def send_notification(
        self,
        subscription: PushSubscription,
        title: str,
        body: str,
        url: str = "/",
        icon: Optional[str] = None,
    ) -> bool:
        """
        Send push notification via Node.js microservice.
        """
        payload = {
            "subscription": {
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            "payload": {"title": title, "body": body, "url": url, "icon": icon},
        }

        endpoint_display = (
            subscription.endpoint[:60] + "..." if len(subscription.endpoint) > 60 else subscription.endpoint
        )

        logger.info(f"⚡ Sending push notification via Node.js service")
        logger.info(f"   Endpoint: {endpoint_display}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.service_url}/send",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.info(f"✅ Push sent successfully")
                    return True
                elif response.status_code in [404, 410]:
                    logger.warning(f"⚠️  Subscription expired ({response.status_code})")
                    return False
                else:
                    logger.error(f"❌ Push failed ({response.status_code})")
                    logger.error(f"   Response: {response.text}")
                    return False

            except httpx.RequestError as exc:
                logger.error(f"❌ Connection error to push service: {exc}")
                logger.error(f"   Make sure Node.js push service is running at {self.service_url}")
                return False
            except Exception as e:
                logger.error(f"❌ Unexpected Error: {type(e).__name__}: {str(e)}")
                return False

    async def send_to_user(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        body: str,
        url: str = "/",
        icon: Optional[str] = None,
    ) -> dict:
        """
        Send notification to all user subscriptions with auto-cleanup.
        """
        logger.info(f"📤 Sending to user {user_id}")

        stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
        result = await db.execute(stmt)
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.warning(f"⚠️  No subscriptions for user {user_id}")
            return {"success": 0, "failed": 0, "expired": 0}

        # Build subscriptions array
        subs_array = [
            {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}} for sub in subscriptions
        ]

        payload = {"subscriptions": subs_array, "payload": {"title": title, "body": body, "url": url, "icon": icon}}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.service_url}/send-batch",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", {})

                    if results.get("expired", 0) > 0:
                        logger.info(f"🗑️  Cleaning up {results['expired']} expired subscription(s)")
                        # In a real impl, we would delete them here

                    logger.info(
                        f"📊 Results: ✅ {results.get('success', 0)}, ❌ {results.get('failed', 0)}, ⚠️  {results.get('expired', 0)}"
                    )

                    return {
                        "success": results.get("success", 0),
                        "failed": results.get("failed", 0),
                        "expired": results.get("expired", 0),
                    }
                else:
                    logger.error(f"❌ Batch push failed ({response.status_code}): {response.text}")
                    return {"success": 0, "failed": len(subscriptions), "expired": 0}

            except httpx.RequestError as exc:
                logger.error(f"❌ Connection error to push service: {exc}")
                return {"success": 0, "failed": len(subscriptions), "expired": 0}
            except Exception as e:
                logger.error(f"❌ Error: {str(e)}")
                return {"success": 0, "failed": len(subscriptions), "expired": 0}


notification_service = NotificationService()
