# FastAPI dependencies for authentication

from fastapi import Request
import logging

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

logger = logging.getLogger(__name__)

def get_graphiti_client(request: Request):
    """Get Graphiti client from app state (Solution 1: shared client with state restoration)."""
    return request.app.state.container.graphiti_client

def get_isolated_graphiti_client(request: Request):
    """
    Get an independent Graphiti client instance per request (Solution 2: isolated client).

    This creates a fresh Graphiti client for each request, ensuring complete isolation
    and preventing global state mutation issues. Each request gets its own driver instance.

    Trade-offs:
    - Pros: Complete isolation, no global state pollution
    - Cons: Higher memory usage, driver connection overhead per request
    """
    from src.configuration.factories import create_graphiti_client
    from src.configuration.config import get_settings

    # Create a new client instance for this request
    client = create_graphiti_client()

    # Log for performance monitoring
    logger.debug(f"Created isolated Graphiti client instance: {id(client)}")

    return client

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
    "get_isolated_graphiti_client",
    "get_queue_service",
]
