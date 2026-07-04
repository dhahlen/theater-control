"""In-memory state model, the single source of truth for the front end.

A background poller refreshes device status and updates this model. Changes are
published to connected WebSocket clients as deltas through the event bus.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from ..adapters.base import DeviceStatus, Reachability


@dataclass
class DeviceState:
    """The last-known state of a single device, as seen by the front end."""

    device_id: str
    reachable: str = Reachability.UNKNOWN.value
    power: str | None = None
    input: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    updated_at: float = 0.0

    @classmethod
    def from_status(cls, status: DeviceStatus, *, now: float) -> "DeviceState":
        return cls(
            device_id=status.device_id,
            reachable=status.reachable.value,
            power=status.power,
            input=status.input,
            extra=dict(status.extra),
            updated_at=now,
        )


class StateStore:
    """Thread-safe-enough (single event loop) store of device state."""

    def __init__(self) -> None:
        self._devices: dict[str, DeviceState] = {}
        self._lock = asyncio.Lock()

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of all device state."""

        return {
            "devices": {did: asdict(ds) for did, ds in self._devices.items()},
            "server_time": time.time(),
        }

    def get(self, device_id: str) -> DeviceState | None:
        return self._devices.get(device_id)

    async def update_from_status(self, status: DeviceStatus) -> DeviceState:
        """Store a fresh status and return the stored state."""

        async with self._lock:
            state = DeviceState.from_status(status, now=time.time())
            self._devices[status.device_id] = state
            return state

    async def set_field(self, device_id: str, **fields: Any) -> DeviceState | None:
        """Patch specific fields on an existing device state (optimistic UI)."""

        async with self._lock:
            state = self._devices.get(device_id)
            if state is None:
                return None
            for key, value in fields.items():
                if key == "extra" and isinstance(value, dict):
                    state.extra.update(value)
                elif hasattr(state, key):
                    setattr(state, key, value)
                else:
                    state.extra[key] = value
            state.updated_at = time.time()
            return state
