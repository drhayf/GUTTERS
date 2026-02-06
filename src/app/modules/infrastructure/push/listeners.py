from src.app.core.events.bus import get_event_bus
from src.app.modules.infrastructure.push.map import EVENT_MAP
from src.app.modules.infrastructure.push.router import notification_router


async def register_listeners():
    """
    Register Notification Router listeners to the Event Bus.
    Dynamically subscribes to all events defined in the Notification Map.

    Note: This function is async because EventBus.subscribe() is async.
    """
    bus = get_event_bus()

    for event_type in EVENT_MAP.keys():
        await bus.subscribe(event_type, notification_router.handle_event_packet)
