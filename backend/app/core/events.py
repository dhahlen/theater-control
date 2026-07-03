"""Event bus that fans out state changes and routine progress to WebSockets.

The API layer subscribes each connected WebSocket to this bus. Adapters, the
poller, and orchestration routines publish events; every subscriber receives a
copy. Publishing never blocks on a slow client: a full queue drops the oldest
message so a stalled iPad cannot back up the whole system.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any, AsyncIterator

MAX_QUEUE = 256


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    async def publish(self, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            _offer(queue, event)

    @contextlib.asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=MAX_QUEUE)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


def _offer(queue: asyncio.Queue[dict[str, Any]], event: dict[str, Any]) -> None:
    """Enqueue, dropping the oldest event if the subscriber is not keeping up."""

    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        with contextlib.suppress(asyncio.QueueEmpty):
            queue.get_nowait()
        with contextlib.suppress(asyncio.QueueFull):
            queue.put_nowait(event)


def device_event(device_id: str, state: dict[str, Any]) -> dict[str, Any]:
    return {"type": "device", "device_id": device_id, "state": state}


def progress_event(scene: str, step: dict[str, Any]) -> dict[str, Any]:
    return {"type": "progress", "scene": scene, "step": step}


def routine_event(scene: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"type": "routine", "scene": scene, "result": result}
