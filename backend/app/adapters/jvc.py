"""JVC DLA-NZ900 adapter.

Protocol: TCP port 20554, NZ-series SHA256 auth (sha256(password + "JVCKWPJ")).
See docs/devices/jvc-nz900.md. This adapter wraps the proven MIT-licensed
``pyjvcprojector`` library, which owns the binary framing, the PJ_OK/PJREQ/PJACK
handshake, NZ authentication, and per-model command maps. The adapter maps the
library surface onto the common DeviceAdapter contract and normalizes values.

The library object is injected so the adapter is unit-testable with a fake
projector and no hardware. See tests/test_jvc.py.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.jvc")

JVC_PORT = 20554

# Picture-mode tokens differ in spelling: our config and capabilities use
# underscores; the library uses hyphens. Translate at the boundary.
def _to_library_value(value: str) -> str:
    return value.replace("_", "-")


def _from_library_value(value: str) -> str:
    return value.replace("-", "_")


class JvcAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        password: str,
        port: int = JVC_PORT,
        projector: Any | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._password = password
        self._projector = projector
        self._connect_lock = asyncio.Lock()

    # -- library plumbing -------------------------------------------------

    def _build_projector(self) -> Any:
        # Imported lazily so the module (and its tests) load without the
        # optional dependency present until a real projector is constructed.
        from jvcprojector import JvcProjector

        return JvcProjector(
            host=self._host, port=self._port, password=self._password
        )

    async def _ensure_connected(self) -> Any:
        async with self._connect_lock:
            if self._projector is None:
                self._projector = self._build_projector()
            await self._projector.connect()
            return self._projector

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        await self._ensure_connected()

    async def disconnect(self) -> None:
        if self._projector is not None:
            try:
                await self._projector.disconnect()
            except Exception as exc:
                log.debug("jvc disconnect error: %s", exc)

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        from jvcprojector import command

        try:
            proj = await self._ensure_connected()
            power = await proj.get(command.Power)
            input_ = None
            low_latency = None
            signal = None
            if power == "on":
                # These reads are only meaningful when the unit is on.
                input_ = await proj.get(command.Input)
                low_latency = await proj.get(command.LowLatencyMode)
                signal = await proj.get(command.Signal)
        except Exception as exc:
            log.debug("jvc get_status failed: %s", exc)
            return DeviceStatus(device_id=self.device_id, reachable=Reachability.OFFLINE)

        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE,
            power=power,
            input=input_,
            extra={
                "low_latency": low_latency,
                "source_status": signal,
            },
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command_name: str, params: dict[str, Any] | None = None) -> Any:
        from jvcprojector import command

        params = params or {}
        proj = await self._ensure_connected()

        if command_name == "power":
            state = _require(params, "state", {"on", "off"})
            await proj.set(command.Power, state)
            return {"power": state}

        if command_name == "input_mode":
            value = _require(params, "input", {"hdmi1", "hdmi2"})
            await proj.set(command.Input, value)
            return {"input": value}

        if command_name == "low_latency":
            state = _require(params, "state", {"on", "off"})
            await proj.set(command.LowLatencyMode, state)
            return {"low_latency": state}

        if command_name == "picture_mode":
            mode = params.get("mode")
            if not mode:
                raise ValueError("picture_mode requires a 'mode' parameter")
            await proj.set(command.PictureMode, _to_library_value(mode))
            return {"picture_mode": mode}

        raise ValueError(f"unknown jvc command {command_name!r}")

    async def read_power(self) -> str | None:
        from jvcprojector import command

        proj = await self._ensure_connected()
        return await proj.get(command.Power)

    async def wait_until_power(self, target: str, timeout_s: float = 60.0) -> bool:
        """Poll power until it equals target (e.g. "on") or timeout.

        Power-on is asynchronous: the unit passes through transitional states
        before reporting "on". The Theater On routine depends on this.
        """

        deadline = asyncio.get_event_loop().time() + timeout_s
        while asyncio.get_event_loop().time() < deadline:
            try:
                if await self.read_power() == target:
                    return True
            except Exception as exc:
                log.debug("jvc power poll error: %s", exc)
            await asyncio.sleep(2.0)
        return False

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("power", {"state": ["on", "off"]}, "Power on/off"),
            Capability("input_mode", {"input": ["hdmi1", "hdmi2"]}, "Select input"),
            Capability("low_latency", {"state": ["on", "off"]}, "Low latency mode"),
            Capability(
                "picture_mode",
                {"mode": ["frame_adapt_hdr", "frame_adapt_hdr2", "frame_adapt_hdr3",
                          "hdr_plus", "hdr", "hlg", "pana_pq", "filmmaker", "film",
                          "cinema", "natural", "thx", "user1", "user2", "user3",
                          "user4", "user5", "user6"]},
                "Picture mode",
            ),
        ]


def _require(params: dict[str, Any], key: str, allowed: set[str]) -> str:
    value = params.get(key)
    if value not in allowed:
        raise ValueError(f"{key} must be one of {sorted(allowed)}, got {value!r}")
    return value
