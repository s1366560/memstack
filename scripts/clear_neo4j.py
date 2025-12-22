import argparse
import sys

from neo4j import GraphDatabase

from server.config import get_settings


def clear_neo4j(force=False):
    settings = get_settings()

    uri = settings.neo4j_uri
    user = settings.neo4j_user
    password = settings.neo4j_password

    print(f"Connecting to Neo4j at {uri}...")

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))

        # Verify connection
        driver.verify_connectivity()
        print("Connected successfully.")

        if not force:
            response = input(
                "⚠️  WARNING: This will delete ALL data AND SCHEMA (Constraints & Indexes) in the Neo4j database. Are you sure? (y/N): "
            )
            if response.lower() != "y":
                print("Operation cancelled.")
                return

        with driver.session() as session:
            # 1. Clear Data
            print("1. Clearing database data (Nodes & Relationships)...")
            result = session.run("MATCH (n) DETACH DELETE n")
            summary = result.consume()

            nodes_deleted = summary.counters.nodes_deleted
            relationships_deleted = summary.counters.relationships_deleted

            print("   ✅ Data cleared.")
            print(f"      - Nodes deleted: {nodes_deleted}")
            print(f"      - Relationships deleted: {relationships_deleted}")

            # 2. Clear Schema (Constraints)
            print("2. Clearing Schema - Constraints...")
            constraints = session.run("SHOW CONSTRAINTS")
            constraint_names = [record["name"] for record in constraints]

            dropped_constraints = 0
            for name in constraint_names:
                try:
                    session.run(f"DROP CONSTRAINT {name}")
                    dropped_constraints += 1
                except Exception as e:
                    print(f"      ⚠️ Failed to drop constraint {name}: {e}")
            print(f"   ✅ Constraints dropped: {dropped_constraints}")

            # 3. Clear Schema (Indexes)
            print("3. Clearing Schema - Indexes...")
            indexes = session.run("SHOW INDEXES")
            # Filter out LOOKUP indexes (usually system maintained)
            index_names = [record["name"] for record in indexes if record["type"] != "LOOKUP"]

            dropped_indexes = 0
            for name in index_names:
                try:
                    session.run(f"DROP INDEX {name}")
                    dropped_indexes += 1
                except Exception as e:
                    # Ignore errors if index was already dropped (e.g. via constraint drop)
                    if "does not exist" not in str(e):
                        print(f"      ⚠️ Failed to drop index {name}: {e}")
            print(f"   ✅ Indexes dropped: {dropped_indexes}")

            # 4. Verify Data is empty
            count_result = session.run("MATCH (n) RETURN count(n) as count")
            count = count_result.single()["count"]
            if count == 0:
                print("4. Verification passed: Database data is empty.")
            else:
                print(f"4. ⚠️  Verification failed: {count} nodes remaining.")

        driver.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear all data and schema from Neo4j database.")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    clear_neo4j(force=args.force)
