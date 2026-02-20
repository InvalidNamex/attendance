"""
Realtime WebSocket manager for broadcasting database changes.
No external dependencies — pure FastAPI WebSocket implementation.
"""
from fastapi import WebSocket
from typing import Dict, Any, List
import json
import asyncio


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts events.
    Database-agnostic — works with any backend.
    """

    def __init__(self):
        self._connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        if websocket in self._connections:
            self._connections.remove(websocket)

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def _send(self, websocket: WebSocket, message: str):
        """Send to a single client, remove if broken."""
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)

    async def broadcast(self, event: str, table: str, data: Dict[str, Any]):
        """
        Broadcast a change event to ALL connected clients.

        Parameters
        ----------
        event : str
            One of "INSERT", "UPDATE", "DELETE".
        table : str
            The table that changed, e.g. "transactions".
        data : dict
            The record payload (or {"id": ...} for deletes).
        """
        if not self._connections:
            return

        message = json.dumps({
            "event": event,
            "table": table,
            "data": data,
        })

        await asyncio.gather(
            *(self._send(ws, message) for ws in list(self._connections)),
            return_exceptions=True,
        )


# Singleton — imported by routers and main.py
manager = ConnectionManager()
