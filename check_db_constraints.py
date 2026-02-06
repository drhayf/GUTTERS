import asyncio

from sqlalchemy import text

from src.app.core.db.database import local_session


async def check_constraints():
    async with local_session() as session:
        # SQL query from user request
        query = text("""
            SELECT
                conname AS constraint_name,
                contype AS constraint_type
            FROM pg_constraint
            WHERE conrelid = 'chat_sessions'::regclass
              AND contype = 'u';
        """)
        result = await session.execute(query)
        rows = result.fetchall()

        print(f"Found {len(rows)} unique constraints on chat_sessions:")
        for row in rows:
            print(f"- {row.constraint_name} (type: {row.constraint_type})")

        # Also check indices just in case
        print("\nChecking indices:")
        query_idx = text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'chat_sessions';
        """)
        result_idx = await session.execute(query_idx)
        for row in result_idx.fetchall():
            print(f"- {row.indexname}: {row.indexdef}")


if __name__ == "__main__":
    asyncio.run(check_constraints())
