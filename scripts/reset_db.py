
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from server.config import get_settings
from server.database import Base
from server.db_models import * # Import all models to ensure metadata is populated

async def reset_database():
    settings = get_settings()
    print(f"Resetting database at {settings.postgres_url}...")
    
    engine = create_async_engine(settings.postgres_url)
    
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    await engine.dispose()
    print("Database reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_database())
