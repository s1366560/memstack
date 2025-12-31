#!/usr/bin/env python3
"""
Database migration management CLI.

Usage:
    python scripts/manage_migrations.py status      - Show migration status
    python scripts/manage_migrations.py apply       - Apply pending migrations
    python scripts/manage_migrations.py check       - Check schema compatibility
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.adapters.secondary.persistence.database import async_session_factory, engine
from src.infrastructure.adapters.secondary.persistence.migrations import (
    apply_migrations as apply_db_migrations,
    get_migration_status as get_db_migration_status,
    check_schema_compatibility as check_db_schema_compatibility,
)
from src.infrastructure.adapters.secondary.persistence.models import Base


async def show_status():
    """Show current migration status."""
    print("\n" + "=" * 80)
    print("DATABASE MIGRATION STATUS")
    print("=" * 80 + "\n")

    # Check if database is accessible
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"❌ Cannot connect to database: {e}")
        return

    # Get migration status
    async with async_session_factory() as session:
        status = await get_db_migration_status(session)

    print(f"Total migrations defined: {status['total_migrations']}")
    print(f"Applied migrations: {len(status['applied_migrations'])}")
    print(f"Pending migrations: {len(status['pending_migrations'])}")

    if status['applied_migrations']:
        print("\n✅ Applied migrations:")
        for mig in status['applied_migrations']:
            print(f"   ✓ {mig['table']}.{mig['column']}")
            if mig.get('description'):
                print(f"     {mig['description']}")

    if status['pending_migrations']:
        print("\n⏳ Pending migrations:")
        for mig in status['pending_migrations']:
            print(f"   ○ {mig['table']}.{mig['column']}")
            if mig.get('description'):
                print(f"     {mig['description']}")

    print("\n" + "=" * 80 + "\n")


async def apply_pending_migrations():
    """Apply all pending migrations."""
    print("\n" + "=" * 80)
    print("APPLYING DATABASE MIGRATIONS")
    print("=" * 80 + "\n")

    # Get current status
    async with async_session_factory() as session:
        status = await get_db_migration_status(session)

    if not status['pending_migrations']:
        print("✅ No pending migrations - database is up to date!\n")
        return

    print(f"Found {len(status['pending_migrations'])} pending migration(s):\n")
    for mig in status['pending_migrations']:
        print(f"  - {mig['table']}.{mig['column']}")
        if mig.get('description'):
            print(f"    {mig['description']}")

    print("\nApplying migrations...\n")

    try:
        async with async_session_factory() as session:
            await apply_db_migrations(session)

        print("\n✅ All migrations applied successfully!\n")

        # Show updated status
        await show_status()

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def check_compatibility():
    """Check if database schema is compatible with models."""
    print("\n" + "=" * 80)
    print("CHECKING SCHEMA COMPATIBILITY")
    print("=" * 80 + "\n")

    async with async_session_factory() as session:
        is_compatible = await check_db_schema_compatibility(session)

    if is_compatible:
        print("✅ Database schema is compatible with models\n")
    else:
        print("⚠️  Database schema may have incompatibilities\n")
        print("Recommendation: Run 'python scripts/manage_migrations.py apply'\n")


async def create_all_tables():
    """Create all tables from scratch (DESTRUCTIVE - use with caution)."""
    print("\n" + "=" * 80)
    print("CREATING ALL TABLES")
    print("=" * 80 + "\n")

    confirm = input("⚠️  This will create all tables from scratch. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        return

    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Tables created successfully\n")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database migration management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status     Show migration status
  %(prog)s apply      Apply pending migrations
  %(prog)s check      Check schema compatibility
  %(prog)s create     Create all tables (use with caution)
        """
    )

    parser.add_argument(
        'command',
        choices=['status', 'apply', 'check', 'create'],
        help='Command to execute'
    )

    args = parser.parse_args()

    if args.command == 'status':
        await show_status()
    elif args.command == 'apply':
        await apply_pending_migrations()
    elif args.command == 'check':
        await check_compatibility()
    elif args.command == 'create':
        await create_all_tables()


if __name__ == "__main__":
    asyncio.run(main())
