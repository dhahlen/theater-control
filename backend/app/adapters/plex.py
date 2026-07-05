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
        chosen = self._session_for_player(sessions)
        now_playing = _summarize_session(chosen) if chosen else None
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

    def _session_for_player(self, sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Pick the session on this adapter's target player, else the first one.

        With a shared server, the Pool House adapter must report its own player's
        session rather than whatever happens to be first in the list.
        """

        if self._default_player_id:
            for session in sessions:
                player = session.get("Player", {}) or {}
                if player.get("machineIdentifier") == self._default_player_id:
                    return session
        return sessions[0] if sessions else None

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

    # -- cover art proxy --------------------------------------------------

    async def fetch_art(self, path: str, width: int = 320, height: int = 480) -> tuple[bytes, str]:
        """Fetch and size a Plex image, keeping the token server-side.

        ``path`` is an internal Plex image path (for example a session's
        ``thumb``/``art``). Only internal paths are accepted so this cannot be
        used to fetch arbitrary URLs. The image is run through Plex's photo
        transcoder to bound its size for the panel.
        """

        if not path.startswith("/") or "://" in path:
            raise ValueError("art path must be an internal Plex path")
        resp = await self._http().get(
            "/photo/:/transcode",
            params={"url": path, "width": width, "height": height, "minSize": 1},
            headers={"Accept": "image/*"},
        )
        resp.raise_for_status()
        return resp.content, resp.headers.get("content-type", "image/jpeg")

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("play", {}, "Resume playback on the target player"),
            Capability("pause", {}, "Pause the target player"),
            Capability("stop", {}, "Stop the target player"),
        ]


def _summarize_session(meta: dict[str, Any]) -> dict[str, Any]:
    """Extract cover art, playback state, and media/file details for the UI.

    Parsing is defensive: Plex omits fields depending on media type and whether
    the stream is transcoded, so every lookup tolerates a missing key.
    """

    player = meta.get("Player", {}) or {}
    session = meta.get("Session", {}) or {}
    media = (meta.get("Media") or [{}])[0]
    part = (media.get("Part") or [{}])[0]
    transcode = meta.get("TranscodeSession") or {}

    def _num(value: Any) -> float | int | None:
        return value if isinstance(value, (int, float)) else None

    # TV episodes: build an "S02E04"-style label when the indices are present.
    episode = None
    if meta.get("type") == "episode":
        season = meta.get("parentIndex")
        number = meta.get("index")
        if isinstance(season, int) and isinstance(number, int):
            episode = f"S{season:02d}E{number:02d}"

    duration_ms = _num(meta.get("duration"))
    return {
        "title": meta.get("title"),
        "type": meta.get("type"),
        "grandparent_title": meta.get("grandparentTitle"),
        "episode": episode,
        "year": meta.get("year"),
        "content_rating": meta.get("contentRating"),
        "runtime_min": round(duration_ms / 60000) if duration_ms else None,
        "genres": [g.get("tag") for g in (meta.get("Genre") or []) if g.get("tag")][:3],
        "ratings": _parse_ratings(meta),
        "summary": meta.get("summary"),
        "state": player.get("state"),
        "player": player.get("title") or player.get("product"),
        # Progress.
        "duration_ms": duration_ms,
        "offset_ms": _num(meta.get("viewOffset")),
        # Cover art / backdrop (internal Plex paths; proxied by /api/plex/art).
        "thumb": meta.get("thumb") or meta.get("grandparentThumb"),
        "art": meta.get("art"),
        # Media / file details.
        "bitrate": _num(media.get("bitrate")),           # kbps
        "resolution": media.get("videoResolution"),
        "width": _num(media.get("width")),
        "height": _num(media.get("height")),
        "dynamic_range": _dynamic_range(media, part),
        "video_codec": media.get("videoCodec"),
        "audio_codec": media.get("audioCodec"),
        "audio_channels": _num(media.get("audioChannels")),
        "frame_rate": media.get("videoFrameRate"),
        "container": media.get("container") or part.get("container"),
        "file": part.get("file"),
        "file_size": _num(part.get("size")),             # bytes
        # Direct play vs transcode.
        "video_decision": transcode.get("videoDecision"),
        "audio_decision": transcode.get("audioDecision"),
        "transcoding": bool(transcode),
        "bandwidth": _num(session.get("bandwidth")),     # kbps reserved
    }


def _parse_ratings(meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize Plex's Rating array into [{source, value}] for TMDB/RT/IMDb."""

    sources = {"imdb": "IMDb", "themoviedb": "TMDB", "rottentomatoes": "RT"}
    out: list[dict[str, Any]] = []
    for rating in meta.get("Rating") or []:
        image = str(rating.get("image", ""))
        value = rating.get("value")
        source = next((label for key, label in sources.items() if key in image), None)
        if source and value is not None:
            out.append({"source": source, "value": value})
    return out


def _dynamic_range(media: dict[str, Any], part: dict[str, Any]) -> str | None:
    """Best-effort HDR/Dolby Vision/HLG detection from the video stream."""

    streams = part.get("Stream") or []
    video = next((s for s in streams if s.get("streamType") == 1), {})
    if video.get("DOVIPresent") or media.get("DOVIPresent"):
        return "Dolby Vision"
    trc = str(video.get("colorTrc", "")).lower()
    if trc == "smpte2084":
        return "HDR10"
    if trc == "arib-std-b67":
        return "HLG"
    return None
