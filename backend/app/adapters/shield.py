"""Nvidia Shield (Android TV) adapter over ADB.

For non-Plex sources (Netflix, Prime Video, Apple TV, YouTube, etc.) there is no
Plex session, so now-playing comes from the Shield itself over ADB on TCP 5555.
``dumpsys media_session`` yields the active app's playback state and metadata, and
the foreground activity names the app; transport is sent with media key events.

ADB requires a one-time on-screen authorization: with "Network debugging" enabled
on the Shield, the first connection prompts to trust this client's RSA key. The
key is generated and stored under ``key_dir`` (mount a writable volume so it
persists across container restarts and the prompt is not repeated).

The shell coroutine is injected so parsing and command mapping are unit-testable
without a device. See docs/devices/nvidia-shield.md.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any, Awaitable, Callable

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.shield")

# Media key events (Android KeyEvent codes).
KEYCODES: dict[str, int] = {
    "play_pause": 85,
    "play": 126,
    "pause": 127,
    "stop": 86,
    "next": 87,
    "previous": 88,
    "rewind": 89,
    "fast_forward": 90,
    "home": 3,
    "back": 4,
}

# Friendly names for common Android TV packages.
APP_NAMES: dict[str, str] = {
    "com.netflix.mediaclient": "Netflix",
    "com.amazon.amazonvideo.livingroom": "Prime Video",
    "com.apple.atve.androidtv.appletv": "Apple TV",
    "com.google.android.youtube.tv": "YouTube",
    "com.google.android.youtube.tvunplugged": "YouTube TV",
    "com.disney.disneyplus": "Disney+",
    "com.wbd.stream": "Max",
    "com.hbo.hbonow": "Max",
    "tv.twitch.android.app": "Twitch",
    "com.plexapp.android": "Plex",
    "com.spotify.tv.android": "Spotify",
    "com.google.android.apps.tv.launcherx": "Home",
    "com.nvidia.tegrazone3": "Shield Home",
    "com.google.android.tvlauncher": "Home",
}

_PLAYBACK_STATE = {0: None, 1: "stopped", 2: "paused", 3: "playing", 6: "buffering", 8: "connecting"}

ShellFn = Callable[[str], Awaitable[str]]


class ShieldAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        port: int = 5555,
        key_dir: str = "/data",
        auth_timeout_s: float = 30.0,
        shell: ShellFn | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._key_dir = key_dir
        self._auth_timeout = auth_timeout_s
        self._shell_fn = shell  # injected in tests
        self._device: Any = None
        self._connect_lock = asyncio.Lock()

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        await self._ensure_connected()

    async def _ensure_connected(self) -> None:
        if self._shell_fn is not None:
            return
        async with self._connect_lock:
            if self._shell_fn is not None:
                return
            from adb_shell.adb_device_async import AdbDeviceTcpAsync

            device = AdbDeviceTcpAsync(self._host, self._port, default_transport_timeout_s=9.0)
            await device.connect(rsa_keys=[self._signer()], auth_timeout_s=self._auth_timeout)
            self._device = device
            self._shell_fn = device.shell
            log.info("shield %s connected over adb", self.device_id)

    def _signer(self) -> Any:
        from adb_shell.auth.keygen import keygen
        from adb_shell.auth.sign_pythonrsa import PythonRSASigner

        key = os.path.join(self._key_dir, "adbkey")
        if not os.path.isfile(key):
            os.makedirs(self._key_dir, exist_ok=True)
            keygen(key)
            log.info("shield %s generated adb key at %s; accept the prompt on the TV", self.device_id, key)
        with open(key) as fh:
            priv = fh.read()
        with open(key + ".pub") as fh:
            pub = fh.read()
        return PythonRSASigner(pub, priv)

    async def disconnect(self) -> None:
        if self._device is not None:
            try:
                await self._device.close()
            except Exception:
                pass
            self._device = None
            self._shell_fn = None

    async def _shell(self, command: str) -> str:
        if self._shell_fn is None:
            raise ConnectionError("shield adb not connected")
        result = await self._shell_fn(command)
        return result or ""

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        try:
            await self._ensure_connected()
            media = await self._shell("dumpsys media_session")
            focus = await self._shell(
                "dumpsys activity activities | grep -E 'mResumedActivity|mCurrentFocus'"
            )
        except Exception as exc:
            log.debug("shield %s status failed: %s", self.device_id, exc)
            # A dead connection must be rebuilt on the next poll.
            self._shell_fn = None
            self._device = None
            return DeviceStatus(device_id=self.device_id, reachable=Reachability.OFFLINE)

        session = _parse_media_session(media)
        foreground = _parse_foreground(focus)
        package = (session or {}).get("package") or foreground
        app_name = APP_NAMES.get(package or "", package)
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE,
            power="on",
            input=app_name,
            extra={
                "app": package,
                "app_name": app_name,
                "foreground": APP_NAMES.get(foreground or "", foreground),
                "title": (session or {}).get("title"),
                "subtitle": (session or {}).get("subtitle"),
                "state": (session or {}).get("state"),
            },
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        await self._ensure_connected()

        if command in KEYCODES:
            await self._shell(f"input keyevent {KEYCODES[command]}")
            return {"sent": command}
        if command == "launch":
            package = params.get("package")
            if not package:
                raise ValueError("launch requires a 'package'")
            await self._shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")
            return {"launched": package}
        raise ValueError(f"unknown shield command {command!r}")

    def capabilities(self) -> list[Capability]:
        keys = sorted(KEYCODES)
        return [
            *[Capability(k, {}, f"Send the {k.replace('_', ' ')} key") for k in keys],
            Capability("launch", {"package": []}, "Launch an app by package name"),
        ]


def _parse_media_session(text: str) -> dict[str, Any] | None:
    """Extract the active app's package, playback state, and title metadata.

    ``dumpsys media_session`` lists one block per session; the playing session
    (state 3) is preferred, then paused, then whatever is present.
    """

    sessions: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.strip()
        pkg = re.search(r"package=(\S+)", line)
        if pkg:
            if current.get("package"):
                sessions.append(current)
            current = {"package": pkg.group(1)}
        state = re.search(r"state=PlaybackState\s*\{state=(\d+)", line)
        if state:
            current["state_code"] = int(state.group(1))
        desc = re.search(r"description=(.+)$", line)
        if desc:
            current["description"] = desc.group(1).strip()
    if current.get("package"):
        sessions.append(current)
    if not sessions:
        return None

    playing = [s for s in sessions if s.get("state_code") == 3]
    paused = [s for s in sessions if s.get("state_code") == 2]
    chosen = (playing or paused or sessions)[0]

    parts = [p.strip() for p in (chosen.get("description") or "").split(",")]
    parts = [p for p in parts if p and p.lower() != "null"]
    return {
        "package": chosen["package"],
        "state": _PLAYBACK_STATE.get(chosen.get("state_code")),
        "title": parts[0] if parts else None,
        "subtitle": parts[1] if len(parts) > 1 else None,
    }


def _parse_foreground(text: str) -> str | None:
    """Pull the foreground package from the resumed/focused activity line."""

    for pattern in (r"mResumedActivity[^\n]*?\s(\S+?)/", r"mCurrentFocus[^\n]*?\s(\S+?)/"):
        m = re.search(pattern, text)
        if m:
            return m.group(1).lstrip("{")
    return None
