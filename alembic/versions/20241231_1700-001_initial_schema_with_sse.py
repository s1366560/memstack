"""Initial migration with existing schema including SSE fields

Revision ID: 001
Revises:
Create Date: 2024-12-31 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema with all tables including SSE fields."""

    # Create users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR PRIMARY KEY,
            email VARCHAR NOT NULL,
            hashed_password VARCHAR NOT NULL,
            full_name VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            is_superuser BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        );
    """)

    # Create tenants table
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            slug VARCHAR NOT NULL UNIQUE,
            description VARCHAR,
            owner_id VARCHAR REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        );
    """)

    # Create projects table
    op.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            description VARCHAR,
            tenant_id VARCHAR REFERENCES tenants(id),
            owner_id VARCHAR REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        );
    """)

    # Create entity_types table
    op.execute("""
        CREATE TABLE IF NOT EXISTS entity_types (
            id VARCHAR PRIMARY KEY,
            project_id VARCHAR REFERENCES projects(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            description VARCHAR,
            schema JSONB DEFAULT '{}',
            status VARCHAR DEFAULT 'ENABLED',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_entity_type_project_name UNIQUE (project_id, name)
        );
    """)

    # Create memories table
    op.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id VARCHAR PRIMARY KEY,
            project_id VARCHAR REFERENCES projects(id),
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            content_type VARCHAR(20) DEFAULT 'text',
            tags JSONB DEFAULT '[]',
            entities JSONB DEFAULT '[]',
            relationships JSONB DEFAULT '[]',
            version INTEGER DEFAULT 1,
            author_id VARCHAR REFERENCES users(id),
            collaborators JSONB DEFAULT '[]',
            is_public BOOLEAN DEFAULT FALSE,
            status VARCHAR DEFAULT 'ENABLED',
            processing_status VARCHAR DEFAULT 'PENDING',
            meta JSONB DEFAULT '{}',
            task_id VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        );
    """)

    # Create task_logs table with SSE fields
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_logs (
            id VARCHAR PRIMARY KEY,
            task_group_id VARCHAR NOT NULL,
            task_type VARCHAR NOT NULL,
            status VARCHAR DEFAULT 'PENDING',
            progress INTEGER DEFAULT 0,
            result JSONB,
            message VARCHAR,
            entity_id VARCHAR,
            entity_type VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE
        );
    """)

    # Create user_projects table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_projects (
            user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
            project_id VARCHAR REFERENCES projects(id) ON DELETE CASCADE,
            role VARCHAR NOT NULL DEFAULT 'member',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (user_id, project_id)
        );
    """)

    # Create user_tenants table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_tenants (
            user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
            tenant_id VARCHAR REFERENCES tenants(id) ON DELETE CASCADE,
            role VARCHAR NOT NULL DEFAULT 'member',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (user_id, tenant_id)
        );
    """)


def downgrade() -> None:
    """Drop all tables."""
    op.execute("DROP TABLE IF EXISTS user_tenants CASCADE;")
    op.execute("DROP TABLE IF EXISTS user_projects CASCADE;")
    op.execute("DROP TABLE IF EXISTS task_logs CASCADE;")
    op.execute("DROP TABLE IF EXISTS memories CASCADE;")
    op.execute("DROP TABLE IF EXISTS entity_types CASCADE;")
    op.execute("DROP TABLE IF EXISTS projects CASCADE;")
    op.execute("DROP TABLE IF EXISTS tenants CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
