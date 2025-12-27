"""
WebSocket Connection Manager for Voice Journal.

Manages WebSocket connections per user, enabling real-time updates
when journal entries are processed.

Best Practices for Azure Container Apps:
- Uses in-memory storage (works with single replica or sticky sessions)
- Implements keepalive pings to prevent Azure's 4-minute idle timeout
- Handles graceful disconnection and cleanup
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from uuid import UUID
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections organized by user ID.
    
    Each user can have multiple connections (multiple browser tabs).
    Messages are broadcast to all connections for a given user.
    """
    
    def __init__(self):
        # Map of user_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> user_id for reverse lookup
        self._websocket_to_user: Dict[WebSocket, str] = {}
        # Keepalive task reference
        self._keepalive_task: Optional[asyncio.Task] = None
        # Flag to stop keepalive when shutting down
        self._running = False
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Accept a new WebSocket connection and register it for a user.
        
        Args:
            websocket: The WebSocket connection
            user_id: The authenticated user's ID
        """
        await websocket.accept()
        
        if user_id not in self._connections:
            self._connections[user_id] = set()
        
        self._connections[user_id].add(websocket)
        self._websocket_to_user[websocket] = user_id
        
        logger.info(f"WebSocket connected for user {user_id}. "
                   f"Total connections for user: {len(self._connections[user_id])}")
        
        # Start keepalive if not running
        if not self._running:
            self._start_keepalive()
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        user_id = self._websocket_to_user.pop(websocket, None)
        
        if user_id and user_id in self._connections:
            self._connections[user_id].discard(websocket)
            
            # Clean up empty user sets
            if not self._connections[user_id]:
                del self._connections[user_id]
            
            logger.info(f"WebSocket disconnected for user {user_id}. "
                       f"Remaining connections: {len(self._connections.get(user_id, []))}")
        
        # Stop keepalive if no connections
        if not self._connections and self._running:
            self._stop_keepalive()
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Send a message to all connections for a specific user.
        
        Args:
            user_id: The user ID to send to
            message: The message dict to send (will be JSON serialized)
            
        Returns:
            Number of connections the message was sent to
        """
        if user_id not in self._connections:
            logger.debug(f"No active connections for user {user_id}")
            return 0
        
        sent_count = 0
        failed_connections = []
        
        for websocket in self._connections[user_id]:
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                failed_connections.append(websocket)
        
        # Clean up failed connections
        for ws in failed_connections:
            self.disconnect(ws)
        
        logger.debug(f"Sent message to {sent_count} connections for user {user_id}")
        return sent_count
    
    async def broadcast_entry_update(self, user_id: str, entry_data: Dict[str, Any]) -> int:
        """
        Broadcast an entry update to a user.
        
        Args:
            user_id: The user who owns the entry
            entry_data: The entry data to send
            
        Returns:
            Number of connections notified
        """
        message = {
            "type": "entry_updated",
            "data": entry_data
        }
        return await self.send_to_user(user_id, message)
    
    def _start_keepalive(self) -> None:
        """Start the keepalive ping task."""
        if self._keepalive_task is None or self._keepalive_task.done():
            self._running = True
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())
            logger.info("Started WebSocket keepalive task")
    
    def _stop_keepalive(self) -> None:
        """Stop the keepalive ping task."""
        self._running = False
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
            logger.info("Stopped WebSocket keepalive task")
    
    async def _keepalive_loop(self) -> None:
        """
        Send periodic pings to keep connections alive.
        
        Azure Container Apps has a 4-minute idle timeout.
        We ping every 30 seconds to stay well under that limit.
        """
        while self._running:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                
                if not self._connections:
                    continue
                
                ping_message = {"type": "ping"}
                failed_connections = []
                
                for user_id, websockets in list(self._connections.items()):
                    for websocket in list(websockets):
                        try:
                            await websocket.send_json(ping_message)
                        except Exception:
                            failed_connections.append(websocket)
                
                # Clean up failed connections
                for ws in failed_connections:
                    self.disconnect(ws)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in keepalive loop: {e}")
    
    @property
    def active_connections_count(self) -> int:
        """Get total number of active connections across all users."""
        return sum(len(sockets) for sockets in self._connections.values())
    
    @property
    def active_users_count(self) -> int:
        """Get number of users with active connections."""
        return len(self._connections)


# Singleton instance
connection_manager = ConnectionManager()
