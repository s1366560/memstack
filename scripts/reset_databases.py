#!/usr/bin/env python3
"""
Script to reset PostgreSQL and Neo4j databases for development testing.
WARNING: This will delete ALL data in the configured databases.
"""

import asyncio
import sys
import os
import argparse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from neo4j import GraphDatabase

# Add project root to path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.configuration.config import get_settings
except ImportError:
    # Fallback if src is not found (e.g. running from wrong dir)
    print("Error: Could not import src.configuration.config. Make sure you are running from the project root.")
    sys.exit(1)

async def reset_postgres(settings):
    """Truncate all tables in PostgreSQL."""
    print(f"🔌 Connecting to PostgreSQL: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    
    engine = create_async_engine(settings.postgres_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Get all table names in public schema
            # We use a PL/pgSQL block to truncate all tables
            print("🗑️  Truncating all tables in PostgreSQL...")
            await conn.execute(text("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """))
            
            print("✅ PostgreSQL data cleared.")
            
    except Exception as e:
        print(f"❌ Error resetting PostgreSQL: {e}")
        raise
    finally:
        await engine.dispose()

def reset_neo4j_sync(settings):
    """Delete all nodes and relationships in Neo4j (Sync version)."""
    print(f"🔌 Connecting to Neo4j: {settings.neo4j_uri}")
    
    driver = GraphDatabase.driver(
        settings.neo4j_uri, 
        auth=(settings.neo4j_user, settings.neo4j_password)
    )
    
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            print("🗑️  Deleting all nodes and relationships in Neo4j...")
            result = session.run("MATCH (n) DETACH DELETE n")
            summary = result.consume()
            print(f"✅ Neo4j data cleared. Deleted {summary.counters.nodes_deleted} nodes and {summary.counters.relationships_deleted} relationships.")
    except Exception as e:
        print(f"❌ Error resetting Neo4j: {e}")
        raise
    finally:
        driver.close()

async def main():
    parser = argparse.ArgumentParser(description="Reset PostgreSQL and Neo4j databases.")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    settings = get_settings()

    if not args.force:
        print("⚠️  WARNING: This will DELETE ALL DATA in the following databases:")
        print(f"  - PostgreSQL: {settings.postgres_db} at {settings.postgres_host}")
        print(f"  - Neo4j: {settings.neo4j_uri}")
        print("Are you sure you want to continue? (y/N)")
        
        choice = input().lower()
        if choice != 'y':
            print("Operation cancelled.")
            sys.exit(0)

    print("\n🚀 Starting database reset...\n")
    
    # Run resets
    try:
        await reset_postgres(settings)
        # Run Neo4j reset (sync)
        reset_neo4j_sync(settings)
        
        print("\n✨ All databases have been reset successfully!")
        
    except Exception as e:
        print(f"\n❌ Reset failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
