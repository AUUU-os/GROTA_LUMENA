from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from corex.config import settings
from sqlmodel import SQLModel

# Create Async Engine
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False, 
    future=True
)

async def init_db():
    """Initialize database tables"""
    from . import models # Ensure models are registered
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead of create_all
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """Dependency for getting async session"""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
