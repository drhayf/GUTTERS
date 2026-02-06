from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_current_user
from src.app.core.config import settings
from src.app.core.db.database import async_get_db
from src.app.models.push import PushSubscription

router = APIRouter(prefix="/push", tags=["push"])


class SubscriptionSchema(BaseModel):
    endpoint: str
    keys: dict


@router.get("/public-key")
async def get_vapid_public_key(current_user: Annotated[Dict[str, Any], Depends(get_current_user)]):
    """
    Returns the VAPID public key for the frontend to subscribe.
    """
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="VAPID keys not configured in server.")
    return {"publicKey": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe")
async def subscribe_push(
    subscription: SubscriptionSchema,
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: AsyncSession = Depends(async_get_db),
):
    """
    Saves a push subscription for the current user.
    """
    # Check if exists
    stmt = select(PushSubscription).where(
        PushSubscription.endpoint == subscription.endpoint, PushSubscription.user_id == current_user["id"]
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # Update keys just in case
        existing.p256dh = subscription.keys.get("p256dh", "")
        existing.auth = subscription.keys.get("auth", "")
        await db.commit()
        return {"message": "Subscription updated"}

    new_sub = PushSubscription(
        user_id=current_user["id"],
        endpoint=subscription.endpoint,
        p256dh=subscription.keys.get("p256dh", ""),
        auth=subscription.keys.get("auth", ""),
    )
    db.add(new_sub)
    await db.commit()
    return {"message": "Subscribed successfully"}


@router.delete("/subscribe")
async def unsubscribe_push(
    subscription: SubscriptionSchema,
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: AsyncSession = Depends(async_get_db),
):
    """
    Removes a specific push subscription for the current user.
    """
    stmt = select(PushSubscription).where(
        PushSubscription.endpoint == subscription.endpoint, PushSubscription.user_id == current_user["id"]
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return {"message": "Unsubscribed successfully"}

    # If not found, it's already gone, essentially success
    return {"message": "Subscription not found or already deleted"}


@router.post("/test")
async def send_test_notification(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)], db: AsyncSession = Depends(async_get_db)
):
    """
    Sends a test notification to all the user's subscriptions.
    """
    from src.app.modules.infrastructure.push.service import notification_service

    results = await notification_service.send_to_user(
        db=db, user_id=current_user["id"], title="Cosmic Alert", body="The universe is speaking. Listen.", url="/"
    )

    return {"results": results}
