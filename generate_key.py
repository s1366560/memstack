import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy import select

from server.auth import create_api_key, create_user
from server.database import async_session_factory
from server.db_models import User


async def main():
    print("Connecting to database...")
    async with async_session_factory() as db:
        email = "admin@vipmemory.com"
        # Find user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"Creating default user {email}...")
            user = await create_user(
                db,
                email=email,
                name="Default Admin",
                role="admin",
            )
        else:
            print(f"Found existing user {email}")

        # Create new API key
        print("Generating new API Key...")
        plain_key, api_key = await create_api_key(
            db,
            user_id=user.id,
            name="Manual Generated Key",
            permissions=["read", "write", "admin"],
        )

        print("\n" + "=" * 50)
        print(f"🔑 NEW API KEY: {plain_key}")
        print("=" * 50 + "\n")
        print("Please copy this key and paste it into the Settings page in the frontend.")


if __name__ == "__main__":
    asyncio.run(main())
