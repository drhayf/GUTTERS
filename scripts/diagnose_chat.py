import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app.modules.features.chat.master_chat import MasterChatHandler

# Mock/Setup DB
DATABASE_URL = "postgresql+asyncpg://postgres.xrihizuhwdbvzhjebwov:!Ch4ng3Th1sP4ssW0rd!@aws-0-us-west-1.pooler.supabase.com:5432/postgres"


async def test_history():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        handler = MasterChatHandler()
        # Test for user 78 (as seen in logs)
        user_id = 78

        print(f"Checking conversations for user {user_id}...")
        convs = await handler.get_conversation_list(user_id, db)
        print(f"Found {len(convs)} conversations.")
        for c in convs:
            print(f"ID: {c['id']}, Name: {c['name']}, Count: {c['message_count']}")

        if convs:
            target_id = convs[0]["id"]
            print(f"\nFetching history for conversation {target_id}...")
            history = await handler.get_conversation_history(user_id, 100, db, session_id=target_id)
            print(f"Found {len(history)} messages.")
            for m in history:
                print(f"[{m['role']}] {m['content'][:50]}... (Metadata keys: {list(m['metadata'].keys())})")


if __name__ == "__main__":
    asyncio.run(test_history())
