"""
Seed demo users for testing and development.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.context import CryptContext

from src.infrastructure.adapters.secondary.persistence.models import User, UserRole, Role

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_demo_users():
    """Create demo users for testing."""

    # Create database engine
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost/memstack"
    )

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Check if users already exist
            result = await session.execute(select(User).where(User.email.in_(["admin@memstack.ai", "user@memstack.ai"])))
            existing_users = result.scalars().all()

            if existing_users:
                print(f"Demo users already exist ({len(existing_users)} found)")
                for user in existing_users:
                    print(f"  - {user.email}")
                return

            # Check if roles exist
            result = await session.execute(select(Role).where(Role.name.in_(["admin", "user"])))
            roles = {role.name: role for role in result.scalars().all()}

            if not roles:
                # Create roles
                admin_role = Role(name="admin", description="Administrator with full access")
                user_role = Role(name="user", description="Regular user with limited access")
                session.add(admin_role)
                session.add(user_role)
                await session.flush()

                roles = {"admin": admin_role, "user": user_role}
                print("Created roles")
            else:
                print(f"Roles already exist: {list(roles.keys())}")

            # Create admin user
            admin_user = User(
                email="admin@memstack.ai",
                name="Admin User",
                password_hash=pwd_context.hash("adminpassword"),
                is_active=True,
                profile={"title": "Administrator", "department": "IT"}
            )
            session.add(admin_user)
            await session.flush()

            # Assign admin role
            admin_user_role = UserRole(user_id=admin_user.id, role_id=roles["admin"].id)
            session.add(admin_user_role)

            # Create regular user
            regular_user = User(
                email="user@memstack.ai",
                name="Demo User",
                password_hash=pwd_context.hash("userpassword"),
                is_active=True,
                profile={"title": "Demo User", "department": "Sales"}
            )
            session.add(regular_user)
            await session.flush()

            # Assign user role
            user_role_mapping = UserRole(user_id=regular_user.id, role_id=roles["user"].id)
            session.add(user_role_mapping)

            await session.commit()

            print("✅ Demo users created successfully:")
            print(f"  - admin@memstack.ai / adminpassword (Admin)")
            print(f"  - user@memstack.ai / userpassword (User)")

    except Exception as e:
        print(f"❌ Error creating demo users: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Creating demo users...")
    asyncio.run(create_demo_users())
