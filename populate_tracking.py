"""
Manually trigger tracking updates for all users to populate initial data
"""
import asyncio
from src.app.modules.tracking.solar.tracker import SolarTracker
from src.app.modules.tracking.lunar.tracker import LunarTracker
from src.app.core.db.database import local_session
from src.app.models.user import User
from sqlalchemy import select

async def populate_tracking_data():
    """Trigger tracking updates for all users"""
    solar = SolarTracker()
    lunar = LunarTracker()
    
    async with local_session() as db:
        result = await db.execute(select(User.id))
        user_ids = [row[0] for row in result.fetchall()]
        
    print(f"Found {len(user_ids)} users")
    
    for user_id in user_ids:
        print(f"\nUpdating tracking for user {user_id}...")
        try:
            solar_result = await solar.update(user_id)
            print(f"  Solar: {solar_result['current_data']['kp_index']} Kp")
            
            lunar_result = await lunar.update(user_id)
            print(f"  Lunar: {lunar_result['current_data']['phase_name']}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n✅ Tracking data populated!")

if __name__ == "__main__":
    asyncio.run(populate_tracking_data())
