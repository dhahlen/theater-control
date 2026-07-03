"""AVPro AC-MX-44X matrix switch adapter (Phase 2 stub).

Documented, not built. The AC-MX-44X moves the gaming PC between the theater
projector chain (Output 1) and the pool house LG display (Output 2). It speaks a
line protocol over TCP 23 (or RS-232 at 57600); ``GET STA`` reads routing, and
routing commands set input-to-output maps.

This stub keeps the phase 2 device in the same adapter shape so it slots into
the architecture without rework. Phase 1 orchestration does not construct it.
See docs/devices/avpro-ac-mx-44x.md.
"""

from __future__ import annotations

from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

ACMX_TCP_PORT = 23


class AcMx44xAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        port: int = ACMX_TCP_PORT,
        inputs: dict[str, int] | None = None,
        outputs: dict[str, int] | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._inputs = dict(inputs or {})
        self._outputs = dict(outputs or {})

    async def connect(self) -> None:
        raise NotImplementedError("AC-MX-44X is a Phase 2 device; not built yet")

    async def disconnect(self) -> None:
        return None

    async def get_status(self) -> DeviceStatus:
        return DeviceStatus(device_id=self.device_id, reachable=Reachability.UNKNOWN)

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError("AC-MX-44X is a Phase 2 device; not built yet")

    def capabilities(self) -> list[Capability]:
        return [
            Capability("route", {"input": sorted(self._inputs), "output": sorted(self._outputs)},
                       "Route an input to an output (Phase 2)"),
        ]
