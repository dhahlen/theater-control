"""MiniDSP SHD adapter (via the minidsp-rs daemon).

The SHD's DSP is controlled over USB, so a small daemon (``minidspd`` from the
minidsp-rs project) runs on the host with the SHD on USB and exposes an HTTP API.
This adapter talks to that daemon, not the SHD directly. Because theater-control
runs with host networking, the daemon is reached on ``127.0.0.1:5380`` by
default.

In this theater the SHD drives seat transducers (bass shakers): the master
level sets the overall shaker gain, and two outputs feed the seat rows (front on
XLR Out 1, rear on XLR Out 2), each with its own gain and mute so a row can be
turned down or off independently.

The minidsp-rs HTTP shapes used (see its README-API):
  - Status:  GET  /devices/<idx>            -> {master:{volume,mute,preset,source}, output_levels:[...]}
  - Master:  POST /devices/<idx>/config     {"master_status": {"volume": db, "mute": bool}}
  - Output:  POST /devices/<idx>/config     {"outputs": [{"index": n, "gain": db, "mute": bool}]}

The daemon reports master volume/mute but not the configured per-output gain and
mute, so those are tracked optimistically from the last command (like the LG
picture mode). The HTTP client is injected for unit tests.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.minidsp")


class MiniDspAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str = "127.0.0.1",
        port: int = 5380,
        device_index: int = 0,
        outputs: dict[str, int] | None = None,
        presets: list[str] | None = None,
        master_min_db: float = -80.0,
        output_min_db: float = -40.0,
        output_max_db: float = 0.0,
        client: Any | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._index = device_index
        self._outputs = dict(outputs or {})
        self._presets = list(presets or [])
        self._master_min = master_min_db
        self._output_min = output_min_db
        self._output_max = output_max_db
        self._client = client

        # Master volume/mute are readable; cache the last-read volume so relative
        # steps have a base. Per-output gain/mute are not reported, so remember
        # what we set to echo it back to the UI.
        self._volume: float | None = None
        self._mute: bool = False
        self._out_gain: dict[int, float] = {}
        self._out_mute: dict[int, bool] = {}

    def _http(self) -> Any:
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=f"http://{self._host}:{self._port}", timeout=4.0
            )
        return self._client

    def _dev(self) -> str:
        return f"/devices/{self._index}"

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        try:
            resp = await self._http().get(self._dev())
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            log.debug("minidsp get_status failed: %s", exc)
            return DeviceStatus(device_id=self.device_id, reachable=Reachability.OFFLINE)

        master = data.get("master", {}) if isinstance(data, dict) else {}
        self._volume = master.get("volume", self._volume)
        self._mute = bool(master.get("mute", self._mute))
        extra: dict[str, Any] = {
            "volume": self._volume,
            "mute": self._mute,
            "source": master.get("source"),
            "preset": master.get("preset"),
            "presets": self._presets,
            "sources": data.get("available_sources", []),
            "output_levels": data.get("output_levels", []),
            "outputs": self._outputs,
            # Optimistic per-output state, keyed by output name for the UI.
            "output_gain": {name: self._out_gain.get(idx) for name, idx in self._outputs.items()},
            "output_mute": {name: self._out_mute.get(idx, False) for name, idx in self._outputs.items()},
            "master_min": self._master_min,
            "output_min": self._output_min,
            "output_max": self._output_max,
        }
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE,
            power="on",
            extra=extra,
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}

        if command == "volume_set":
            db = _clamp(_as_number(params, "db"), self._master_min, 0.0)
            await self._post({"master_status": {"volume": db}})
            self._volume = db
            return {"volume": db}

        if command == "volume_adjust":
            base = self._volume if self._volume is not None else self._master_min
            db = _clamp(base + _as_number(params, "delta"), self._master_min, 0.0)
            await self._post({"master_status": {"volume": db}})
            self._volume = db
            return {"volume": db}

        if command == "mute":
            state = _on_off(params)
            await self._post({"master_status": {"mute": state}})
            self._mute = state
            return {"mute": state}

        if command == "output_gain":
            index = self._resolve_output(params)
            db = _clamp(_as_number(params, "db"), self._output_min, self._output_max)
            await self._post({"outputs": [{"index": index, "gain": db}]})
            self._out_gain[index] = db
            return {"index": index, "gain": db}

        if command == "output_mute":
            index = self._resolve_output(params)
            state = _on_off(params)
            await self._post({"outputs": [{"index": index, "mute": state}]})
            self._out_mute[index] = state
            return {"index": index, "mute": state}

        if command == "source":
            source = params.get("source")
            if not source:
                raise ValueError("source requires a 'source' name")
            await self._post({"master_status": {"source": source}})
            return {"source": source}

        if command == "preset":
            preset = int(_as_number(params, "index"))
            await self._post({"master_status": {"preset": preset}})
            return {"preset": preset}

        raise ValueError(f"unknown minidsp command {command!r}")

    async def _post(self, body: dict[str, Any]) -> None:
        resp = await self._http().post(f"{self._dev()}/config", json=body)
        resp.raise_for_status()

    def _resolve_output(self, params: dict[str, Any]) -> int:
        if "index" in params:
            return int(params["index"])
        name = params.get("name")
        if name is None:
            raise ValueError("output requires 'index' or 'name'")
        if name not in self._outputs:
            raise ValueError(f"unknown output {name!r}; known: {sorted(self._outputs)}")
        return self._outputs[name]

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("volume_set", {"db": []}, "Set master level (dB)"),
            Capability("volume_adjust", {"delta": []}, "Step master level (dB)"),
            Capability("mute", {"state": ["on", "off"]}, "Master mute on/off"),
            Capability("output_gain", {"name": sorted(self._outputs), "db": []}, "Set an output's gain (dB)"),
            Capability("output_mute", {"name": sorted(self._outputs), "state": ["on", "off"]}, "Mute an output on/off"),
            Capability("source", {"source": []}, "Select input source"),
            Capability("preset", {"index": []}, "Recall a config preset"),
        ]


def _as_number(params: dict[str, Any], key: str) -> float:
    if key not in params:
        raise ValueError(f"missing required parameter {key!r}")
    try:
        return float(params[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number") from exc


def _on_off(params: dict[str, Any]) -> bool:
    state = params.get("state")
    if state not in ("on", "off"):
        raise ValueError("state must be 'on' or 'off'")
    return state == "on"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
