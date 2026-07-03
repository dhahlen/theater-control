"""JVC DLA-NZ900 adapter (scaffold).

Protocol: TCP port 20554, NZ-series SHA256 auth (sha256(password + "JVCKWPJ")).
See docs/devices/jvc-nz900.md. A proven reference implementation is
iloveicedgreentea/jvc_projector_python (MIT) which may be used directly.

This scaffold defines the shape; the implementing agent fills in the transport.
"""

from __future__ import annotations

from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

JVC_PORT = 20554


class JvcAdapter(DeviceAdapter):
    def __init__(self, device_id: str, host: str, password: str,
                 port: int = JVC_PORT) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._password = password  # hashed internally per NZ-series auth

    async def connect(self) -> None:
        raise NotImplementedError

    async def disconnect(self) -> None:
        raise NotImplementedError

    async def get_status(self) -> DeviceStatus:
        # Return power ("standby"|"on"|"cooling"|...), current input, low_latency,
        # source_status ("logo"|"no_signal"|"signal") in extra.
        raise NotImplementedError

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        # Supported: power(on|off), input_mode(hdmi1|hdmi2),
        # low_latency(on|off), picture_mode(frame_adapt_hdr|...).
        raise NotImplementedError

    async def wait_until_power(self, target: str, timeout_s: float = 60.0) -> bool:
        """Poll power until it equals target (e.g. "on") or timeout.

        The Theater On routine depends on this. See docs/usecases/theater-on.md.
        """
        raise NotImplementedError

    def capabilities(self) -> list[Capability]:
        return [
            Capability("power", {"state": ["on", "off"]}, "Power on/off"),
            Capability("input_mode", {"input": ["hdmi1", "hdmi2"]}, "Select input"),
            Capability("low_latency", {"state": ["on", "off"]}, "Low latency mode"),
            Capability(
                "picture_mode",
                {"mode": ["frame_adapt_hdr", "hdr_plus", "hdr", "hlg",
                          "filmmaker", "film", "cinema", "natural", "thx",
                          "user1", "user2", "user3", "user4", "user5", "user6"]},
                "Picture mode",
            ),
        ]
