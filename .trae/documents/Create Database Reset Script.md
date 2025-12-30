I have created a Python script `scripts/reset_databases.py` that clears both PostgreSQL and Neo4j databases.

### Features:
1.  **PostgreSQL Reset**: Connects to the database configured in `src.configuration.config` and truncates all tables in the `public` schema using `TRUNCATE ... CASCADE`. This preserves the schema structure but removes all data.
2.  **Neo4j Reset**: Connects to the Neo4j instance and executes `MATCH (n) DETACH DELETE n` to remove all nodes and relationships.
3.  **Safety**: Includes a confirmation prompt ("Are you sure? y/N") to prevent accidental data loss.
4.  **Force Mode**: Supports a `--force` flag to skip the confirmation prompt for automated environments.

### Usage:
-   **Run interactively**: `python3 scripts/reset_databases.py`
-   **Run without confirmation**: `python3 scripts/reset_databases.py --force`

The script automatically loads your project's configuration (host, port, credentials) so no manual configuration is needed.