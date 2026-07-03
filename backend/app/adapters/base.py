"""Common adapter interface for all theater devices.

Every device adapter implements this interface so that orchestration routines
and the API treat all devices uniformly. Adapters own their transport,
handshake/authentication, retries, and status parsing. Adapters must not
import from the api or orchestration packages.

This is scaffold: method bodies are intentionally left for the implementing
agent. See docs/ARCHITECTURE.md and the per-device specs in docs/devices/.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Reachability(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class DeviceStatus:
    """Normalized status returned by every adapter's get_status()."""

    device_id: str
    reachable: Reachability = Reachability.UNKNOWN
    power: str | None = None            # e.g. "on", "standby", "cooling"
    input: str | None = None            # current input/source, friendly name
    # Device-specific fields (volume, profile, signal, now_playing, etc.)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Capability:
    """Declares one command the device supports, for dynamic UI/API."""

    name: str
    params: dict[str, list[str]] = field(default_factory=dict)  # param -> allowed values
    description: str = ""


class DeviceAdapter(ABC):
    """Base contract for all device adapters."""

    device_id: str

    @abstractmethod
    async def connect(self) -> None:
        """Establish transport, including handshake/authentication."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down the transport cleanly."""

    @abstractmethod
    async def get_status(self) -> DeviceStatus:
        """Return normalized status with no side effects."""

    @abstractmethod
    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a named capability with validated parameters."""

    @abstractmethod
    def capabilities(self) -> list[Capability]:
        """Declare supported commands so the UI/API can render controls."""

    async def health(self) -> Reachability:
        """Report reachability. Default polls get_status; override for speed."""
        try:
            status = await self.get_status()
            return status.reachable
        except Exception:
            return Reachability.OFFLINE
