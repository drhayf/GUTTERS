import asyncio
from src.app.core.db.database import local_session
from src.app.models.tracking import TrackingSnapshot
from sqlalchemy import select, desc

async def check_db():
    async with local_session() as db:
        # Check solar snapshots
        stmt = select(TrackingSnapshot).where(
            TrackingSnapshot.module == "solar_tracking"
        ).order_by(desc(TrackingSnapshot.timestamp)).limit(1)
        
        result = await db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        
        if snapshot:
            print("Found solar snapshot:")
            print(f"  Timestamp: {snapshot.timestamp}")
            print(f"  Data keys: {list(snapshot.data.keys())}")
            print(f"  Data: {snapshot.data}")
        else:
            print("No solar snapshots found in database")
        
        # Check lunar too
        stmt = select(TrackingSnapshot).where(
            TrackingSnapshot.module == "lunar_tracking"
        ).order_by(desc(TrackingSnapshot.timestamp)).limit(1)
        
        result = await db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        
        if snapshot:
            print("\nFound lunar snapshot:")
            print(f"  Timestamp: {snapshot.timestamp}")
            print(f"  Data keys: {list(snapshot.data.keys())}")
        else:
            print("\nNo lunar snapshots found in database")

asyncio.run(check_db())
