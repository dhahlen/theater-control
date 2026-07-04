"""Trinnov Altitude CI adapter.

Protocol: TCP port 44100, line-oriented ASCII, same-subnet only. On connect the
Altitude sends a welcome banner (``Welcome on Trinnov Optimizer (Version X, ID
n)``); the client then registers with ``id <client_id>``. The processor emits
asynchronous status broadcasts, so this adapter keeps a persistent connection
and parses pushed state rather than polling.

Command and status tokens confirmed against the community reference library
``trinnov-altitude`` (binarylogic), which mirrors the official Trinnov IP
control protocol:
  - volume set (absolute, dB):   ``volume <db>``
  - volume adjust (relative):    ``dvolume <delta>``
  - mute on/off:                 ``mute 1`` / ``mute 0``
  - source/profile select:       ``profile <id>``
  - power off (over IP):         ``power_off_SECURED_FHZMCH48FE``
  - status broadcasts parsed:    ``VOLUME <db>``, ``MUTE <0|1>``,
                                 ``CURRENT_PROFILE <n>``, ``PROFILE <n>: <name>``

See docs/devices/trinnov-altitude.md. The transport is injected so the adapter
is unit-testable without a processor.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..core.transport import LineTransport
from ..core.wol import send_magic_packet
from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.trinnov")

TRINNOV_PORT = 44100
POWER_OFF_COMMAND = "power_off_SECURED_FHZMCH48FE"

_WELCOME = re.compile(r"^Welcome on Trinnov Optimizer \(Version (\S+), ID (\d+)\)$")
_VOLUME = re.compile(r"^VOLUME\s(-?\d+(?:\.\d+)?)$")
_MUTE = re.compile(r"^MUTE\s(0|1)$")
_CURRENT_PROFILE = re.compile(r"^CURRENT_PROFILE\s(-?\d+)$")
_PROFILE_LABEL = re.compile(r"^PROFILE\s(-?\d+): (.*)$")
_CURRENT_PRESET = re.compile(r"^CURRENT_PRESET\s(-?\d+)$")
_PRESET_LABEL = re.compile(r"^LABEL\s(-?\d+): (.*)$")
_UPMIXER = re.compile(r"^UPMIXER\s(.*)$")
_DIM = re.compile(r"^DIM\s(-?\d+)$")
_BYPASS = re.compile(r"^BYPASS\s(0|1)$")
_SRATE = re.compile(r"^SRATE\s(\d+)$")
_SOURCE_FORMAT = re.compile(r"^CURRENT_SOURCE_FORMAT_NAME\s(.*)$")

# Upmixer modes accepted by the "upmixer <mode>" command.
UPMIXER_MODES = ["auto", "native", "dolby", "dts", "auro3d", "legacy", "upmix on native"]


class TrinnovAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        port: int = TRINNOV_PORT,
        sources: dict[str, int] | None = None,
        client_id: str = "theater-control",
        mac: str | None = None,
        transport: LineTransport | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._sources = dict(sources or {})
        self._id_to_source = {v: k for k, v in self._sources.items()}
        self._client_id = client_id
        self._mac = mac
        self._transport = transport

        self._volume: float | None = None
        self._mute: bool | None = None
        self._source_index: int | None = None
        self._labels: dict[int, str] = {}
        self._power = "on"  # assume on once connected; Trinnov has no clean read
        self._presets: dict[int, str] = {}
        self._current_preset: int | None = None
        self._upmixer: str | None = None
        self._dim: bool | None = None
        self._bypass: bool | None = None
        self._srate: int | None = None
        self._source_format: str | None = None

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        if self._transport is None:
            self._transport = LineTransport(
                self._host,
                self._port,
                on_line=self._handle_line,
                on_connect=self._on_connect,
                terminator=b"\n",
            )
        await self._transport.start()

    async def disconnect(self) -> None:
        if self._transport is not None:
            await self._transport.stop()

    async def _on_connect(self) -> None:
        # Register so the processor streams state to us, then prime preset list.
        await self._transport.send_line(f"id {self._client_id}")
        await self._transport.send_line("get_all_label")
        await self._transport.send_line("get_current_preset")

    # -- inbound parsing --------------------------------------------------

    def _handle_line(self, line: str) -> None:
        if _WELCOME.match(line):
            log.info("trinnov welcome: %s", line)
            return
        if m := _VOLUME.match(line):
            self._volume = float(m.group(1))
            return
        if m := _MUTE.match(line):
            self._mute = bool(int(m.group(1)))
            return
        if m := _CURRENT_PROFILE.match(line):
            self._source_index = int(m.group(1))
            return
        if m := _CURRENT_PRESET.match(line):
            self._current_preset = int(m.group(1))
            return
        if m := _PRESET_LABEL.match(line):
            self._presets[int(m.group(1))] = m.group(2)
            return
        if m := _UPMIXER.match(line):
            self._upmixer = m.group(1).strip()
            return
        if m := _DIM.match(line):
            self._dim = bool(int(m.group(1)))
            return
        if m := _BYPASS.match(line):
            self._bypass = bool(int(m.group(1)))
            return
        if m := _SRATE.match(line):
            self._srate = int(m.group(1))
            return
        if m := _SOURCE_FORMAT.match(line):
            self._source_format = m.group(1).strip()
            return
        if m := _PROFILE_LABEL.match(line):
            self._labels[int(m.group(1))] = m.group(2)
            return

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        connected = bool(self._transport and self._transport.connected)
        source_name = None
        if self._source_index is not None:
            source_name = self._id_to_source.get(
                self._source_index, self._labels.get(self._source_index)
            )
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE if connected else Reachability.OFFLINE,
            power=self._power if connected else None,
            input=source_name,
            extra={
                "volume": self._volume,
                "mute": self._mute,
                "source_index": self._source_index,
                "sources": self._sources,
                "presets": {str(k): v for k, v in self._presets.items()},
                "current_preset": self._current_preset,
                "upmixer": self._upmixer,
                "dim": self._dim,
                "bypass": self._bypass,
                "sample_rate": self._srate,
                "source_format": self._source_format,
            },
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}

        if command == "power":
            state = params.get("state")
            if state == "off":
                await self._send(POWER_OFF_COMMAND)
                self._power = "off"
                return {"power": "off"}
            if state == "on":
                if not self._mac:
                    raise ValueError("trinnov power on requires a configured MAC (Wake-on-LAN)")
                send_magic_packet(self._mac)
                self._power = "on"
                return {"power": "on"}
            raise ValueError("power state must be 'on' or 'off'")

        if command == "volume_set":
            db = _as_float(params, "db")
            await self._send(f"volume {round(db, 1)}")
            return {"volume": db}

        if command == "volume_adjust":
            delta = _as_float(params, "delta")
            await self._send(f"dvolume {delta}")
            return {"delta": delta}

        if command == "mute":
            state = params.get("state")
            if state not in ("on", "off"):
                raise ValueError("mute state must be 'on' or 'off'")
            await self._send(f"mute {1 if state == 'on' else 0}")
            self._mute = state == "on"
            return {"mute": self._mute}

        if command == "source":
            source_id = self._resolve_source(params)
            await self._send(f"profile {source_id}")
            return {"source_index": source_id}

        if command == "preset":
            if "index" not in params:
                raise ValueError("preset requires an 'index'")
            index = int(params["index"])
            await self._send(f"loadp {index}")
            return {"preset": index}

        if command == "upmixer":
            mode = params.get("mode")
            if mode not in UPMIXER_MODES:
                raise ValueError(f"mode must be one of {UPMIXER_MODES}, got {mode!r}")
            await self._send(f"upmixer {mode}")
            self._upmixer = mode
            return {"upmixer": mode}

        if command == "dim":
            state = params.get("state")
            if state not in ("on", "off"):
                raise ValueError("dim state must be 'on' or 'off'")
            await self._send(f"dim {1 if state == 'on' else 0}")
            self._dim = state == "on"
            return {"dim": self._dim}

        if command == "bypass":
            state = params.get("state")
            if state not in ("on", "off"):
                raise ValueError("bypass state must be 'on' or 'off'")
            await self._send(f"bypass {1 if state == 'on' else 0}")
            self._bypass = state == "on"
            return {"bypass": self._bypass}

        raise ValueError(f"unknown trinnov command {command!r}")

    def _resolve_source(self, params: dict[str, Any]) -> int:
        if "name" in params:
            name = params["name"]
            if name not in self._sources:
                raise ValueError(f"unknown source name {name!r}; known: {sorted(self._sources)}")
            return self._sources[name]
        if "index" in params:
            return int(params["index"])
        raise ValueError("source requires 'name' or 'index'")

    async def _send(self, line: str) -> None:
        if self._transport is None:
            raise ConnectionError("trinnov transport not started")
        await self._transport.send_line(line)

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("power", {"state": ["on", "off"]}, "Power on/off"),
            Capability("volume_set", {"db": []}, "Set absolute volume in dB"),
            Capability("volume_adjust", {"delta": []}, "Adjust volume by delta dB"),
            Capability("mute", {"state": ["on", "off"]}, "Mute on/off"),
            Capability("source", {"name": sorted(self._sources)}, "Select source/profile"),
            Capability("preset", {"index": []}, "Load a preset by index"),
            Capability("upmixer", {"mode": UPMIXER_MODES}, "Set upmixer mode"),
            Capability("dim", {"state": ["on", "off"]}, "Dim on/off"),
            Capability("bypass", {"state": ["on", "off"]}, "Processing bypass on/off"),
        ]


def _as_float(params: dict[str, Any], key: str) -> float:
    if key not in params:
        raise ValueError(f"missing required parameter {key!r}")
    try:
        return float(params[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number") from exc
