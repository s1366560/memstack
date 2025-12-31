#!/usr/bin/env python3
"""
Alembic CLI helper for MemStack.

This script provides a simple interface to common Alembic commands.
Usage:
    python scripts/alembic_cli.py current      # Show current version
    python scripts/alembic_cli.py history      # Show migration history
    python scripts/alembic_cli.py upgrade      # Apply pending migrations
    python scripts/alembic_cli.py downgrade    # Rollback one version
    python scripts/alembic_cli.py revision     # Create new migration
    python scripts/alembic_cli.py status       # Show detailed status
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
from src.configuration.config import get_settings
from src.infrastructure.adapters.secondary.persistence.alembic_migrations import get_alembic_config


def get_sync_url():
    """Get synchronous database URL for Alembic."""
    settings = get_settings()
    return settings.postgres_url.replace("+asyncpg", "", 1)


def current():
    """Show current database version."""
    config = get_alembic_config()
    config.set_main_option("sqlalchemy.url", get_sync_url())

    try:
        command.current(config)
    except Exception as e:
        print(f"Error: {e}")
        print("\n💡 Tip: If this is a new database, run: python scripts/alembic_cli.py upgrade")


def history():
    """Show migration history."""
    config = get_alembic_config()
    config.set_main_option("sqlalchemy.url", get_sync_url())
    command.history(config)


def upgrade(revision: str = "head"):
    """Upgrade database to a later version."""
    config = get_alembic_config()
    config.set_main_option("sqlalchemy.url", get_sync_url())

    print(f"Upgrading database to {revision}...")
    command.upgrade(config, revision)
    print(f"✅ Upgraded to {revision}")


def downgrade(revision: str = "-1"):
    """Downgrade database to an earlier version."""
    config = get_alembic_config()
    config.set_main_option("sqlalchemy.url", get_sync_url())

    print(f"Downgrading database to {revision}...")
    command.downgrade(config, revision)
    print(f"✅ Downgraded to {revision}")


def revision(message: str, autogenerate: bool = False):
    """Create a new migration."""
    config = get_alembic_config()
    config.set_main_option("sqlalchemy.url", get_sync_url())

    if autogenerate:
        print(f"Creating autogenerate migration: {message}")
        command.revision(config, message=message, autogenerate=True)
    else:
        print(f"Creating empty migration: {message}")
        command.revision(config, message=message)

    print(f"✅ Migration created")


def status():
    """Show detailed migration status."""
    config = get_alembic_config()
    config.set_main_option("sqlalchemy.url", get_sync_url())

    from alembic.script import ScriptDirectory
    script_dir = ScriptDirectory.from_config(config)

    print("\n" + "=" * 80)
    print("ALEMBIC MIGRATION STATUS")
    print("=" * 80 + "\n")

    # Get current version from database
    engine = create_engine(get_sync_url())
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
            print(f"Current database version: {current_version}")
    except Exception:
        print("Current database version: None (no migrations applied)")
        current_version = None
    finally:
        engine.dispose()

    # Get head version
    head = script_dir.get_current_head()
    print(f"Latest migration version: {head}")

    # Get all revisions
    revisions = list(script_dir.walk_revisions())
    print(f"Total migrations available: {len(revisions)}\n")

    if current_version == head:
        print("✅ Database is up to date\n")
    elif current_version is None:
        print("⚠️  No migrations applied yet")
        print(f"   Run: python scripts/alembic_cli.py upgrade\n")
    else:
        print(f"⚠️  Database needs upgrade")
        print(f"   Run: python scripts/alembic_cli.py upgrade\n")

    # Show recent revisions
    if revisions:
        print("Recent migrations:")
        for rev in reversed(revisions[:5]):
            doc = rev.doc if rev.doc else "No description"
            print(f"   {rev.revision} - {doc}")

    print("\n" + "=" * 80 + "\n")


def show_help():
    """Show help message."""
    print("""
Alembic CLI for MemStack

Commands:
    current      Show current database version
    history      Show full migration history
    upgrade      Upgrade to latest version (or specific revision)
    downgrade    Rollback one version (or to specific revision)
    revision     Create a new migration
    status       Show detailed migration status
    help         Show this help message

Examples:
    python scripts/alembic_cli.py status
    python scripts/alembic_cli.py upgrade
    python scripts/alembic_cli.py downgrade -1
    python scripts/alembic_cli.py revision "Add new feature" --autogenerate

For more information, see: docs/alembic_implementation_plan.md
    """)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        return

    command_name = sys.argv[1].lower()

    if command_name == "current":
        current()
    elif command_name == "history":
        history()
    elif command_name == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        upgrade(revision)
    elif command_name == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        downgrade(revision)
    elif command_name == "revision":
        message = sys.argv[2] if len(sys.argv) > 2 else "New migration"
        autogenerate = "--autogenerate" in sys.argv
        revision(message, autogenerate)
    elif command_name == "status":
        status()
    elif command_name == "help":
        show_help()
    else:
        print(f"Unknown command: {command_name}")
        show_help()


if __name__ == "__main__":
    main()
