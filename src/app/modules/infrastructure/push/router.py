import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.core.db.database import local_session as async_session_factory
from src.app.models.user import User
from src.app.models.user_profile import UserProfile
from src.app.modules.infrastructure.push.service import notification_service
from src.app.modules.infrastructure.push.map import EVENT_MAP
from src.app.protocol.packet import Packet

logger = logging.getLogger(__name__)


class NotificationRouter:
    """
    Central router for system events -> push notifications.
    Uses src.app.modules.infrastructure.push.map.EVENT_MAP for configuration.
    """

    async def handle_event_packet(self, packet: Packet):
        """
        Generic handler for all subscribed events.
        """
        event_type = packet.event_type
        payload = packet.payload
        config = EVENT_MAP.get(event_type)

        if not config:
            return  # Should not happen if listeners are wired correctly

        # 1. Check Filter (Global)
        if config.filter_func and not config.filter_func(payload):
            return

        logger.info(f"NotificationRouter: Processing {event_type} (Pref: {config.preference_key})")

        async with async_session_factory() as db:
            # 2. Get Users (Simple Iteration for now, optimized later for scale)
            # Just like before, we iterate all users.
            stmt = select(User).where(User.is_deleted == False)
            result = await db.execute(stmt)
            users = result.scalars().all()

            for user in users:
                try:
                    # 3. Check User Preference
                    # We need to fetch profile efficiently.
                    # N+1 query here, but okay for MVP scale.
                    p_stmt = select(UserProfile).where(UserProfile.user_id == user.id)
                    p_res = await db.execute(p_stmt)
                    profile = p_res.scalar_one_or_none()

                    # Default to TRUE if no profile or no pref set (Opt-out model)
                    should_send = True
                    if profile and profile.data:
                        prefs = profile.data.get("preferences", {}).get("notifications", {})
                        # If key exists, use it. If not, default to True.
                        if config.preference_key in prefs:
                            should_send = prefs[config.preference_key]

                    if not should_send:
                        continue

                    # 4. Format Message
                    # Safe format using .format(**payload) but handling missing keys gracefully?
                    # Python's .format raises KeyError. Let's use a helper or simple logic.
                    try:
                        title = config.title_template.format(**payload)
                        body = config.body_template.format(**payload)
                    except KeyError as e:
                        logger.warning(f"Notification formatting failed for {event_type}: Missing {e}")
                        title = config.title_template  # Fallback
                        body = str(payload)

                    # 5. Send
                    await notification_service.send_to_user(
                        db=db, user_id=user.id, title=title, body=body, url=config.deep_link
                    )

                except Exception as e:
                    logger.error(f"Error sending notification to user {user.id}: {e}")


notification_router = NotificationRouter()
