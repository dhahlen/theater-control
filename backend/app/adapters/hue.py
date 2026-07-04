"""Philips Hue lighting adapter.

Control is via the local Hue Bridge v1 REST API (no cloud dependency). The
existing play-triggered dimming (Lumunarr, driven by Plex start/stop) stays the
source of truth for automatic dimming; this adapter only provides manual scene
recall and group level control in the unified UI, so it must not be wired into
any automatic play trigger.

v1 endpoints used:
  - Recall scene:      PUT /api/<key>/groups/<group>/action  {"scene": "<id>"}
  - Set group level:   PUT /api/<key>/groups/<group>/action  {"on": true, "bri": n}
  - Toggle group:      PUT /api/<key>/groups/<group>/action  {"on": bool}
  - Read group state:  GET /api/<key>/groups/<group>

See docs/devices/philips-hue.md. The bridge uses a self-signed certificate, so
TLS verification is disabled for the LAN connection. The HTTP client is injected
for unit tests.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.hue")

BRI_MAX = 254


class HueAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        bridge_ip: str,
        app_key: str,
        room_group_id: str = "1",
        scenes: dict[str, str] | None = None,
        client: Any | None = None,
    ) -> None:
        self.device_id = device_id
        self._bridge_ip = bridge_ip
        self._app_key = app_key
        self._group = room_group_id
        self._scenes = dict(scenes or {})
        self._client = client

    def _http(self) -> Any:
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=f"https://{self._bridge_ip}",
                verify=False,  # bridge uses a self-signed certificate on the LAN
                timeout=5.0,
            )
        return self._client

    def _base(self) -> str:
        return f"/api/{self._app_key}"

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        # REST is connectionless; nothing to establish.
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
            resp = await self._http().get(f"{self._base()}/groups/{self._group}")
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            log.debug("hue get_status failed: %s", exc)
            return DeviceStatus(device_id=self.device_id, reachable=Reachability.OFFLINE)

        action = data.get("action", {})
        state = data.get("state", {})
        any_on = state.get("any_on")
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE,
            power="on" if any_on else "off",
            extra={
                "bri": action.get("bri"),
                "any_on": any_on,
                "all_on": state.get("all_on"),
                "scenes": list(self._scenes),
            },
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}

        if command == "recall_scene":
            name = params.get("scene")
            scene_id = self._scenes.get(name)
            if not scene_id:
                raise ValueError(f"unknown scene {name!r}; known: {sorted(self._scenes)}")
            await self._group_action({"scene": scene_id})
            return {"scene": name}

        if command == "set_level":
            bri = params.get("bri")
            if not isinstance(bri, (int, float)) or not 0 <= bri <= BRI_MAX:
                raise ValueError(f"bri must be 0..{BRI_MAX}")
            await self._group_action({"on": bri > 0, "bri": int(bri)})
            return {"bri": int(bri)}

        if command == "toggle":
            state = params.get("state")
            if state not in ("on", "off"):
                raise ValueError("toggle state must be 'on' or 'off'")
            await self._group_action({"on": state == "on"})
            return {"on": state == "on"}

        raise ValueError(f"unknown hue command {command!r}")

    async def _group_action(self, body: dict[str, Any]) -> None:
        resp = await self._http().put(
            f"{self._base()}/groups/{self._group}/action", json=body
        )
        resp.raise_for_status()

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("recall_scene", {"scene": sorted(self._scenes)}, "Recall a Hue scene"),
            Capability("set_level", {"bri": []}, "Set group brightness (0-254)"),
            Capability("toggle", {"state": ["on", "off"]}, "Turn the group on/off"),
        ]
