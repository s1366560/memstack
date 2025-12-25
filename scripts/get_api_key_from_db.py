#!/usr/bin/env python3
"""
Get the default API key directly from the database.

This script bypasses the API and reads the API key directly from PostgreSQL.
Use this for development/testing when you need to get the default API key.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from server.database import async_session_factory
from server.db_models import APIKey, User


async def main():
    """Get API keys from database."""
    print("🔑 Fetching API keys from database...")
    print()

    async with async_session_factory() as db:
        try:
            # Get all users
            result = await db.execute(select(User))
            users = result.scalars().all()

            if not users:
                print("No users found in database.")
                print("The server may not have been initialized yet.")
                return

            print(f"Found {len(users)} user(s):")
            print()

            for user in users:
                print(f"  User: {user.name} ({user.email})")
                print(f"    ID: {user.id}")
                print(f"    Role: {user.role}")
                print()

                # Get API keys for this user
                result = await db.execute(select(APIKey).where(APIKey.user_id == user.id))
                keys = result.scalars().all()

                if keys:
                    print(f"    API Keys ({len(keys)}):")
                    for key in keys:
                        print(f"      - {key.name}")
                        print(f"        ID: {key.id}")
                        print(f"        Prefix: {key.key_hash[:16]}...")
                        print(f"        Active: {key.is_active}")
                        print(f"        Created: {key.created_at}")
                        print()
                else:
                    print("    No API keys found for this user")
                    print()

            # Provide instructions
            print("=" * 50)
            print()
            print("⚠️  API keys are stored hashed in the database.")
            print("The actual API key is only shown when it's created.")
            print()
            print("To get the default API key:")
            print("1. Check the server startup logs (look for 'Default Admin API Key created')")
            print("2. Or restart the server to see the key printed again")
            print()
            print("Server startup command:")
            print("  make dev")
            print()
            print("The key will be printed in output like:")
            print("  🔑 Default Admin API Key created: ms_sk_...")
            print()

        except Exception as e:
            print(f"Error: {e}")
            print()
            print("Make sure:")
            print("1. PostgreSQL is running (make docker-up)")
            print("2. The database connection is configured correctly")
            print()


if __name__ == "__main__":
    asyncio.run(main())
