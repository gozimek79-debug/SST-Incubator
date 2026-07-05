"""Tick Stream – forwarduje dane z CLI do WebSocket.

NIE liczy. NIE analizuje. TYLKO forwarduje.
"""

import asyncio
import json
from typing import AsyncIterator
from fastapi import WebSocket


class TickStreamer:
    """Forwarder ticków – zero logiki."""

    def __init__(self):
        self._subscribers: list[WebSocket] = []

    async def subscribe(self, websocket: WebSocket):
        """Dodaj subskrybenta WebSocket."""
        self._subscribers.append(websocket)

    async def unsubscribe(self, websocket: WebSocket):
        """Usuń subskrybenta."""
        if websocket in self._subscribers:
            self._subscribers.remove(websocket)

    async def broadcast(self, tick_data: dict):
        """Wyślij tick do wszystkich subskrybentów."""
        dead = []
        for ws in self._subscribers:
            try:
                await ws.send_json(tick_data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.unsubscribe(ws)

    async def stream_from_generator(self, generator):
        """Konsumuje generator ticków i broadcastuje."""
        for tick_data in generator:
            await self.broadcast(tick_data)
            await asyncio.sleep(0.01)


# Globalna instancja
tick_streamer = TickStreamer()
