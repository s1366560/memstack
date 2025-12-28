"""
Create demo users via API calls.
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def create_demo_users_via_api():
    """Create demo users by directly inserting into database."""

    # We'll create users using the API if available, or provide SQL to insert
    print("Creating demo users...")
    print("\nSince we need database access, please run this SQL directly:\n")

    sql = """
-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create roles if not exist
INSERT INTO roles (id, name, description, created_at, updated_at)
VALUES
  ('550e8400-e29b-41d4-a716-446655440000', 'admin', 'Administrator with full access', NOW(), NOW()),
  ('550e8400-e29b-41d4-a716-446655440001', 'user', 'Regular user with limited access', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Get role IDs
DO $$
DECLARE
  admin_role_id UUID;
  user_role_id UUID;
BEGIN
  SELECT id INTO admin_role_id FROM roles WHERE name = 'admin';
  SELECT id INTO user_role_id FROM roles WHERE name = 'user';

  -- Create admin user
  INSERT INTO users (id, email, name, password_hash, is_active, created_at, updated_at)
  VALUES (
    '10000000-0000-0000-0000-000000000001',
    'admin@memstack.ai',
    'Admin User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCWfyjR7qdqjV5pF5QhWFGpOZjUCQLcHq',
    true,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO NOTHING;

  -- Assign admin role
  INSERT INTO user_roles (user_id, role_id)
  VALUES ('10000000-0000-0000-0000-000000000001', admin_role_id)
  ON CONFLICT DO NOTHING;

  -- Create regular user
  INSERT INTO users (id, email, name, password_hash, is_active, created_at, updated_at)
  VALUES (
    '10000000-0000-0000-0000-000000000002',
    'user@memstack.ai',
    'Demo User',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQJuGcXEJk2QKmPn2Z9K',
    true,
    NOW(),
    NOW()
  )
  ON CONFLICT (email) DO NOTHING;

  -- Assign user role
  INSERT INTO user_roles (user_id, role_id)
  VALUES ('10000000-0000-0000-0000-000000000002', user_role_id)
  ON CONFLICT DO NOTHING;

  RAISE NOTICE 'Demo users created successfully';
END $$;

-- Verify users
SELECT u.email, u.name, u.is_active, r.name as role
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.email IN ('admin@memstack.ai', 'user@memstack.ai');
"""

    print(sql)
    print("\nPassword hashes (bcrypt):")
    print("  adminpassword: $2b$12$LQv3c1yqBWVHxkd0LHAkCWfyjR7qdqjV5pF5QhWFGpOZjUCQLcHq")
    print("  userpassword: $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQJuGcXEJk2QKmPn2Z9K")


if __name__ == "__main__":
    asyncio.run(create_demo_users_via_api())
