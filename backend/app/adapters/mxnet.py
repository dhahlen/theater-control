"""AVPro MXNet distribution adapter (Phase 2 stub).

Documented, not built. MXNet distributes AV over IP via encoders and decoders,
managed through a CBOX controller on Telnet port 24 (``config get version``,
encoder/decoder routing). This stub preserves the adapter shape for phase 2.
Phase 1 orchestration does not construct it. See docs/devices/avpro-mxnet.md.
"""

from __future__ import annotations

from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

MXNET_CBOX_PORT = 24


class MxnetAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        cbox_host: str,
        cbox_port: int = MXNET_CBOX_PORT,
        encoders: dict[str, str] | None = None,
        decoders: dict[str, str] | None = None,
    ) -> None:
        self.device_id = device_id
        self._cbox_host = cbox_host
        self._cbox_port = cbox_port
        self._encoders = dict(encoders or {})
        self._decoders = dict(decoders or {})

    async def connect(self) -> None:
        raise NotImplementedError("MXNet is a Phase 2 device; not built yet")

    async def disconnect(self) -> None:
        return None

    async def get_status(self) -> DeviceStatus:
        return DeviceStatus(device_id=self.device_id, reachable=Reachability.UNKNOWN)

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError("MXNet is a Phase 2 device; not built yet")

    def capabilities(self) -> list[Capability]:
        return [
            Capability("route", {"encoder": sorted(self._encoders), "decoder": sorted(self._decoders)},
                       "Route an encoder to a decoder (Phase 2)"),
        ]
