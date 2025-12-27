"""
WebSocket Router for Voice Journal.

Provides WebSocket endpoint for real-time entry updates.
Authentication is done via query parameter token since WebSocket
doesn't support custom headers in the browser.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.websockets import WebSocketState

from api.auth.utils import decode_access_token
from api.websocket.manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


async def authenticate_websocket(token: Optional[str]) -> Optional[str]:
    """
    Authenticate a WebSocket connection using JWT token.
    
    Args:
        token: JWT access token from query parameter
        
    Returns:
        User ID if authenticated, None otherwise
    """
    if not token:
        logger.warning("WebSocket connection attempt without token")
        return None
    
    payload = decode_access_token(token)
    if not payload:
        logger.warning("WebSocket connection with invalid token")
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("WebSocket token missing user ID")
        return None
    
    return user_id


@router.websocket("/entries")
async def websocket_entries(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT access token")
):
    """
    WebSocket endpoint for real-time entry updates.
    
    Connect with: ws://host/api/v1/ws/entries?token=<jwt_token>
    
    Messages received:
    - {"type": "entry_updated", "data": {...}} - Entry has been processed
    - {"type": "ping"} - Keepalive ping (client should ignore or respond with pong)
    
    Messages sent by client:
    - {"type": "pong"} - Optional response to ping (not required)
    """
    # Authenticate before accepting connection
    user_id = await authenticate_websocket(token)
    
    if not user_id:
        # Close with authentication error
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Accept and register connection
    await connection_manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connection established"
        })
        
        # Keep connection open and handle incoming messages
        while True:
            try:
                # Wait for messages (primarily for pong responses or future features)
                data = await websocket.receive_json()
                
                # Handle pong (optional, just log it)
                if data.get("type") == "pong":
                    logger.debug(f"Received pong from user {user_id}")
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                # Handle JSON parse errors or other issues
                if websocket.client_state == WebSocketState.DISCONNECTED:
                    break
                logger.debug(f"WebSocket receive error: {e}")
                
    finally:
        connection_manager.disconnect(websocket)


@router.get("/status")
async def websocket_status():
    """
    Get WebSocket connection statistics.
    
    Useful for monitoring and debugging.
    """
    return {
        "active_connections": connection_manager.active_connections_count,
        "active_users": connection_manager.active_users_count
    }
