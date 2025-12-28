# FastAPI dependencies for authentication

from fastapi import Request

from src.infrastructure.adapters.primary.web.dependencies.auth_dependencies import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    verify_password,
    get_password_hash,
    get_api_key_from_header,
    verify_api_key_dependency,
    get_current_user,
    create_api_key,
    create_user,
    initialize_default_credentials,
    security,
)

def get_graphiti_client(request: Request):
    """Get Graphiti client from app state."""
    return request.app.state.container.graphiti_client

def get_queue_service(request: Request):
    """Get QueueService from app state."""
    return request.app.state.queue_service

__all__ = [
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "verify_password",
    "get_password_hash",
    "get_api_key_from_header",
    "verify_api_key_dependency",
    "get_current_user",
    "create_api_key",
    "create_user",
    "initialize_default_credentials",
    "security",
    "get_graphiti_client",
    "get_queue_service",
]
