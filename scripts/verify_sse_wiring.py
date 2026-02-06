import asyncio
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.app.core.events.bus import EventBus


async def verify_sse_wiring():
    print("Initializing EventBus...")
    bus = EventBus()
    await bus.initialize()

    event_queue = asyncio.Queue()

    async def queue_handler(packet):
        print(f"Handler received event: {packet.event_type}")
        await event_queue.put(packet)

    print("Subscribing to '*'...")
    await bus.subscribe("*", queue_handler)

    print("Publishing test event...")
    await bus.publish("system.test", {"message": "Hello World"})

    try:
        print("Waiting for event in queue...")
        packet = await asyncio.wait_for(event_queue.get(), timeout=2.0)
        print(f"SUCCESS: Received packet: {packet.event_type}")
    except TimeoutError:
        print("FAILURE: Timed out waiting for event.")
    finally:
        await bus.cleanup()


if __name__ == "__main__":
    asyncio.run(verify_sse_wiring())
