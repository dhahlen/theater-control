"""Plex adapter.

Two HTTP layers exist: the Plex Media Server (PMS) API for now-playing/library,
and the companion remote-control API for driving a player. For phase 1 the
primary deliverable is the embedded Plex Web panel (rendered by the front end),
so this adapter focuses on reporting now-playing sessions for the status bar and
exposing the web URL. Player transport control is an optional enhancement.

The Plex token is never exposed to the front end; it lives only in this adapter,
sourced from the PLEX_TOKEN environment variable. See docs/devices/plex.md.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.plex")


class PlexAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        base_url: str,
        token: str,
        default_player_id: str = "",
        web_url: str = "",
        client: Any | None = None,
    ) -> None:
        self.device_id = device_id
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._default_player_id = default_player_id
        self._web_url = web_url or f"{self._base_url}/web"
        self._client = client

    def _http(self) -> Any:
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={"X-Plex-Token": self._token, "Accept": "application/json"},
                timeout=5.0,
            )
        return self._client

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
            resp = await self._http().get("/status/sessions")
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            log.debug("plex get_status failed: %s", exc)
            return DeviceStatus(
                device_id=self.device_id,
                reachable=Reachability.OFFLINE,
                extra={"web_url": self._web_url},
            )

        container = data.get("MediaContainer", {})
        sessions = container.get("Metadata", []) or []
        now_playing = _summarize_session(sessions[0]) if sessions else None
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE,
            power="on",
            extra={
                "session_count": container.get("size", len(sessions)),
                "now_playing": now_playing,
                "web_url": self._web_url,
            },
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        if command in ("play", "pause", "stop"):
            player = params.get("player") or self._default_player_id
            if not player:
                raise ValueError("no target player configured for Plex transport control")
            await self._companion(f"/player/playback/{command}", player)
            return {"sent": command, "player": player}
        raise ValueError(f"unknown plex command {command!r}")

    async def _companion(self, path: str, player_id: str) -> None:
        resp = await self._http().get(
            path,
            headers={
                "X-Plex-Client-Identifier": "theater-control",
                "X-Plex-Target-Client-Identifier": player_id,
            },
        )
        resp.raise_for_status()

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("play", {}, "Resume playback on the target player"),
            Capability("pause", {}, "Pause the target player"),
            Capability("stop", {}, "Stop the target player"),
        ]


def _summarize_session(meta: dict[str, Any]) -> dict[str, Any]:
    player = meta.get("Player", {}) or {}
    return {
        "title": meta.get("title"),
        "type": meta.get("type"),
        "grandparent_title": meta.get("grandparentTitle"),
        "state": player.get("state"),
        "player": player.get("title"),
    }
