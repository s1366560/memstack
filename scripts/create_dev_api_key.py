#!/usr/bin/env python3
"""
Create a new development API key and display it.

This script creates a fresh API key for testing purposes and displays it.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select

from server.auth import create_api_key
from server.database import async_session_factory
from server.db_models import User


async def main():
    """Create a new API key and display it."""
    print("🔑 Creating new development API key...")
    print()

    # Find the admin user
    async with async_session_factory() as db:
        # Try memstack.ai admin
        result = await db.execute(select(User).where(User.email == "admin@memstack.ai"))
        admin = result.scalar_one_or_none()

        if not admin:
            print("❌ Could not find admin user in database.")
            print()
            print("Please ensure the server has been started at least once")
            print("to initialize the database with default users.")
            return

        # Use the existing create_api_key function
        plain_key, new_key = await create_api_key(
            db,
            user_id=admin.id,
            name="Dev Test API Key",
            permissions=["read", "write"],
        )

        print("=" * 50)
        print()
        print("✅ New API Key Created Successfully!")
        print()
        print(f"Admin User: {admin.name} ({admin.email})")
        print(f"Key Name: {new_key.name}")
        print(f"Key ID: {new_key.id}")
        print()
        print("🔑 Your API Key:")
        print()
        print(f"   {plain_key}")
        print()
        print("=" * 50)
        print()
        print("You can now use this key with:")
        print()
        print("  # Export as environment variable")
        print(f'  export API_KEY="{plain_key}"')
        print("  make test-data")
        print()
        print("  # Or pass directly")
        print(f'  API_KEY="{plain_key}" make test-data')
        print()
        print("  # Or use with the Python script directly")
        print(f'  python scripts/generate_test_data.py --api-key "{plain_key}"')
        print()


if __name__ == "__main__":
    asyncio.run(main())
