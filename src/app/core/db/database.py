from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.pool import NullPool

from ..config import settings


class Base(DeclarativeBase):
    pass


DATABASE_URI = settings.POSTGRES_URI
DATABASE_PREFIX = settings.POSTGRES_ASYNC_PREFIX
DATABASE_URL = f"{DATABASE_PREFIX}{DATABASE_URI}"

# Try session pooler (5432) instead of transaction pooler (6543)
# Session pooler supports prepared statements, which avoids
# DuplicatePreparedStatementError in asyncpg.
DATABASE_URL = DATABASE_URL.replace(":6543/", ":5432/")


async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=False,
    poolclass=NullPool,
    connect_args={
        "server_settings": {
            "jit": "off",
        }
    },
)

local_session = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with local_session() as db:
        yield db
