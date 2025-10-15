"""
Shared database configuration for microservices.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class DatabaseManager:
    """Database manager for microservices."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Close database connection."""
        await self.engine.dispose()


# Global database manager instance
db_manager: DatabaseManager = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance."""
    return db_manager


def init_db_manager(database_url: str):
    """Initialize global database manager."""
    global db_manager
    db_manager = DatabaseManager(database_url)
