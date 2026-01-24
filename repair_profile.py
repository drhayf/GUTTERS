import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "src"))

from app.core.db.database import local_session
from app.models.user import User
from app.models.user_profile import UserProfile
from sqlalchemy import select

async def main():
    async with local_session() as db:
        result = await db.execute(select(User).where(User.id == 4))
        user = result.scalar_one()
        
        # Try setting via relationship instead of user_id directly
        profile = UserProfile(data={})
        profile.user = user
        
        db.add(profile)
        try:
            await db.commit()
            print(f"Profile created for user {user.id} via relationship")
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())
