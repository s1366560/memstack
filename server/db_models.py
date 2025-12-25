from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from server.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tenant_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)

    api_keys: Mapped[List["APIKey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memos: Mapped[List["Memo"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tenants: Mapped[List["UserTenant"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    projects: Mapped[List["UserProject"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memories: Mapped[List["Memory"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    owned_tenants: Mapped[List["Tenant"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    owned_projects: Mapped[List["Project"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    key_hash: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="api_keys")


class Memo(Base):
    __tablename__ = "memos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    visibility: Mapped[str] = mapped_column(String, default="PRIVATE")  # PRIVATE, PUBLIC, PROTECTED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship(back_populates="memos")


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    plan: Mapped[str] = mapped_column(String, default="free")
    max_projects: Mapped[int] = mapped_column(Integer, default=3)
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_storage: Mapped[int] = mapped_column(BigInteger, default=1073741824)  # 1GB
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="owned_tenants")
    users: Mapped[List["UserTenant"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    projects: Mapped[List["Project"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    member_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    memory_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    graph_config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="projects")
    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    users: Mapped[List["UserProject"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    memories: Mapped[List["Memory"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class UserTenant(Base):
    __tablename__ = "user_tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, default="member")  # owner, admin, member, guest
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="tenants")
    tenant: Mapped["Tenant"] = relationship(back_populates="users")


class UserProject(Base):
    __tablename__ = "user_projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, default="member")  # owner, admin, member, viewer
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="projects")
    project: Mapped["Project"] = relationship(back_populates="users")


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), default="text")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    entities: Mapped[list[dict]] = mapped_column(JSON, default=list)
    relationships: Mapped[list[dict]] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    author_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    collaborators: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="memories")
    author: Mapped["User"] = relationship(back_populates="memories")
