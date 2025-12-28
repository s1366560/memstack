from fastapi import Request

def get_graphiti_client(request: Request):
    """Get Graphiti client from app state."""
    return request.app.state.container.graphiti_client

def get_queue_service(request: Request):
    """Get QueueService from app state."""
    return request.app.state.queue_service
