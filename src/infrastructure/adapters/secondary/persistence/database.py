from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.configuration.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.postgres_url, echo=settings.log_level.upper() == "DEBUG")

async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with async_session_factory() as session:
        yield session
