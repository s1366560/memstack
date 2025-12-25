import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

print("Starting init_db.py...")
from server.auth import initialize_default_credentials


async def main():
    print("Calling initialize_default_credentials...")
    await initialize_default_credentials()
    print("Finished initialize_default_credentials.")


if __name__ == "__main__":
    asyncio.run(main())
