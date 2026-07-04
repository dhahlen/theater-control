"""LG G5 (webOS) display adapter.

Control is the LG "SSAP" protocol: a JSON message bus over a WebSocket on
ws://<tv>:3000. On connect the client sends a ``register`` request carrying a
manifest of the permissions it wants. The first time, the TV shows an on-screen
prompt; once accepted it returns a ``client-key`` that is reused on every later
connection to skip the prompt. Store that key in ``LG_CLIENT_KEY`` (.env).

Each command is a request with a unique id; the TV replies with a message
carrying the same id. Power-on is not possible over SSAP (the socket is down
when the panel is off), so it uses Wake-on-LAN like the MadVR and Trinnov.

The WebSocket is injected (``transport_factory``) so the message protocol is
unit-testable without a TV. See docs/devices/lg-g5.md.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

from ..core.wol import send_magic_packet
from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.lg")

# Permissions manifest sent with the register request. Trimmed to the handshake
# webOS requires to grant control; the TV pairs on the client-key it returns.
REGISTER_MANIFEST: dict[str, Any] = {
    "forcePairing": False,
    "pairingType": "PROMPT",
    "manifest": {
        "manifestVersion": 1,
        "permissions": [
            "CONTROL_POWER",
            "CONTROL_AUDIO",
            "CONTROL_INPUT_MEDIA_PLAYBACK",
            "CONTROL_INPUT_TV",
            "READ_TV_CURRENT_CHANNEL",
            "READ_POWER_STATE",
            "READ_CURRENT_CHANNEL",
            "READ_INPUT_DEVICE_LIST",
            "WRITE_SETTINGS",
        ],
    },
}

# Picture presets, mapped to the webOS setSystemSettings "pictureMode" tokens.
PICTURE_MODES: dict[str, str] = {
    "Filmmaker": "filmMaker",
    "Cinema": "cinema",
    "Vivid": "vivid",
    "Standard": "normal",
    "Game": "game",
}


class SsapTransport:
    """Minimal async WebSocket wrapper the adapter drives (send/recv JSON text)."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._ws: Any = None

    async def connect(self) -> None:
        import websockets

        self._ws = await websockets.connect(
            self._url, open_timeout=5, ping_interval=None, max_size=2**22
        )

    async def send(self, message: str) -> None:
        await self._ws.send(message)

    async def recv(self) -> str:
        return await self._ws.recv()

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()


TransportFactory = Callable[[], Any]
KeyHandler = Callable[[str], Awaitable[None] | None]


class LgAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        port: int = 3000,
        client_key: str = "",
        mac: str | None = None,
        inputs: dict[str, str] | None = None,
        transport_factory: TransportFactory | None = None,
        on_client_key: KeyHandler | None = None,
        pair_timeout: float = 60.0,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._client_key = client_key
        self._mac = mac
        self._inputs = dict(inputs or {})
        self._transport_factory = transport_factory
        self._on_client_key = on_client_key
        self._pair_timeout = pair_timeout

        self._transport: Any = None
        self._reader: asyncio.Task[None] | None = None
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._counter = 0
        self._registered = False
        self._power = "off"
        self._connect_lock = asyncio.Lock()
        self._register_id: str | None = None
        self._register_future: asyncio.Future[dict[str, Any]] | None = None

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        # Best-effort at startup; get_status reconnects if the TV was off here.
        await self._ensure_connected()

    async def _ensure_connected(self) -> None:
        """Open and register the socket if it is not already live.

        The panel's SSAP socket is down while the TV is off, so this is retried
        on every poll: once the TV powers on, the adapter reconnects on its own.
        """

        if self._transport is not None and self._registered:
            return
        async with self._connect_lock:
            if self._transport is not None and self._registered:
                return
            await self._teardown()
            if self._transport_factory is not None:
                self._transport = self._transport_factory()
            else:
                self._transport = SsapTransport(f"ws://{self._host}:{self._port}")
            await self._transport.connect()
            self._reader = asyncio.create_task(
                self._read_loop(), name=f"lg:{self.device_id}"
            )
            await self._register()

    async def disconnect(self) -> None:
        async with self._connect_lock:
            await self._teardown()

    async def _teardown(self) -> None:
        self._registered = False
        if self._reader:
            self._reader.cancel()
            try:
                await self._reader
            except asyncio.CancelledError:
                pass
            self._reader = None
        if self._transport is not None:
            try:
                await self._transport.close()
            except Exception:
                pass
            self._transport = None
        for fut in self._pending.values():
            if not fut.done():
                fut.cancel()
        self._pending.clear()

    async def _register(self) -> None:
        payload = dict(REGISTER_MANIFEST)
        if self._client_key:
            payload["client-key"] = self._client_key
        mid = self._next_id("register")
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._register_id = mid
        self._register_future = fut
        await self._transport.send(json.dumps({"id": mid, "type": "register", "payload": payload}))
        # Pairing can require a physical on-screen accept, so wait generously.
        resp = await asyncio.wait_for(fut, timeout=self._pair_timeout)
        key = resp.get("payload", {}).get("client-key")
        if key and key != self._client_key:
            self._client_key = key
            log.info("lg %s paired; store LG_CLIENT_KEY=%s", self.device_id, key)
            if self._on_client_key:
                result = self._on_client_key(key)
                if asyncio.iscoroutine(result):
                    await result
        self._registered = True

    # -- messaging --------------------------------------------------------

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    async def _read_loop(self) -> None:
        try:
            while True:
                raw = await self._transport.recv()
                try:
                    msg = json.loads(raw)
                except (ValueError, TypeError):
                    continue
                mid = msg.get("id")
                if mid and mid == self._register_id:
                    self._handle_register_message(msg)
                    continue
                fut = self._pending.get(mid) if mid else None
                if fut and not fut.done():
                    fut.set_result(msg)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.debug("lg %s read loop ended: %s", self.device_id, exc)
        finally:
            # Mark the link down so the next poll reconnects.
            self._registered = False

    def _handle_register_message(self, msg: dict[str, Any]) -> None:
        fut = self._register_future
        mtype = msg.get("type")
        if mtype == "registered":
            self._register_id = None
            if fut and not fut.done():
                fut.set_result(msg)
        elif mtype == "error":
            self._register_id = None
            if fut and not fut.done():
                fut.set_exception(RuntimeError(msg.get("error") or "lg registration refused"))
        else:
            # Interim prompt: the user must accept pairing on the TV.
            log.info("lg %s waiting for pairing: accept the prompt on the TV", self.device_id)

    async def _send_raw(
        self,
        mtype: str,
        *,
        uri: str | None = None,
        payload: dict[str, Any] | None = None,
        wait_for: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        if self._transport is None:
            raise ConnectionError("lg transport not connected")
        mid = message_id or self._next_id(mtype)
        message: dict[str, Any] = {"id": mid, "type": mtype}
        if uri:
            message["uri"] = uri
        if payload is not None:
            message["payload"] = payload
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[mid] = fut
        try:
            await self._transport.send(json.dumps(message))
            resp = await asyncio.wait_for(fut, timeout=5.0)
        finally:
            self._pending.pop(mid, None)
        if resp.get("type") == "error":
            raise RuntimeError(resp.get("error") or "lg command error")
        if wait_for and resp.get("type") not in (wait_for, "response"):
            raise RuntimeError(f"unexpected lg response {resp.get('type')!r}")
        return resp

    async def _request(self, uri: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._send_raw("request", uri=uri, payload=payload or {})
        return resp.get("payload", {})

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        try:
            await self._ensure_connected()
        except Exception as exc:
            log.debug("lg %s connect failed: %s", self.device_id, exc)
            return DeviceStatus(device_id=self.device_id, reachable=Reachability.OFFLINE)
        extra: dict[str, Any] = {"inputs": self._inputs}
        try:
            vol = await self._request("ssap://audio/getVolume")
            extra["volume"] = vol.get("volume")
            extra["mute"] = vol.get("muted", vol.get("mute"))
            app = await self._request("ssap://com.webos.applicationManager/getForegroundAppInfo")
            extra["app_id"] = app.get("appId")
            self._power = "on"
        except Exception as exc:
            log.debug("lg %s status failed: %s", self.device_id, exc)
            return DeviceStatus(device_id=self.device_id, reachable=Reachability.OFFLINE)
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE,
            power=self._power,
            input=extra.get("app_id"),
            extra=extra,
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}

        # Power-on is Wake-on-LAN and must work while the socket is down; every
        # other command needs a live SSAP connection.
        if not (command == "power" and params.get("state") == "on"):
            await self._ensure_connected()

        if command == "power":
            state = params.get("state")
            if state == "off":
                await self._request("ssap://system/turnOff")
                self._power = "off"
                return {"power": "off"}
            if state == "on":
                if not self._mac:
                    raise ValueError("lg power on requires a configured MAC (Wake-on-LAN)")
                send_magic_packet(self._mac)
                self._power = "on"
                return {"power": "on"}
            raise ValueError("power state must be 'on' or 'off'")

        if command == "volume_set":
            volume = int(_as_number(params, "volume"))
            await self._request("ssap://audio/setVolume", {"volume": volume})
            return {"volume": volume}

        if command == "volume_adjust":
            delta = int(_as_number(params, "delta"))
            uri = "ssap://audio/volumeUp" if delta >= 0 else "ssap://audio/volumeDown"
            for _ in range(abs(delta)):
                await self._request(uri)
            return {"delta": delta}

        if command == "mute":
            state = params.get("state")
            if state not in ("on", "off"):
                raise ValueError("mute state must be 'on' or 'off'")
            await self._request("ssap://audio/setMute", {"mute": state == "on"})
            return {"mute": state == "on"}

        if command == "input":
            input_id = self._resolve_input(params)
            await self._request("ssap://tv/switchInput", {"inputId": input_id})
            return {"input": input_id}

        if command == "picture_mode":
            mode = params.get("mode")
            token = PICTURE_MODES.get(mode)
            if token is None:
                raise ValueError(f"mode must be one of {sorted(PICTURE_MODES)}, got {mode!r}")
            await self._request(
                "ssap://com.webos.service.settings/setSystemSettings",
                {"category": "picture", "settings": {"pictureMode": token}},
            )
            return {"picture_mode": mode}

        raise ValueError(f"unknown lg command {command!r}")

    def _resolve_input(self, params: dict[str, Any]) -> str:
        if "input" in params:
            return str(params["input"])
        if "name" in params:
            name = params["name"]
            if name not in self._inputs:
                raise ValueError(f"unknown input name {name!r}; known: {sorted(self._inputs)}")
            return self._inputs[name]
        raise ValueError("input requires 'input' (HDMI id) or 'name'")

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("power", {"state": ["on", "off"]}, "Power on (Wake-on-LAN) / off"),
            Capability("volume_set", {"volume": []}, "Set absolute volume 0-100"),
            Capability("volume_adjust", {"delta": []}, "Step volume up/down"),
            Capability("mute", {"state": ["on", "off"]}, "Mute on/off"),
            Capability("input", {"name": sorted(self._inputs)}, "Switch HDMI input"),
            Capability("picture_mode", {"mode": sorted(PICTURE_MODES)}, "Set picture mode"),
        ]


def _as_number(params: dict[str, Any], key: str) -> float:
    if key not in params:
        raise ValueError(f"missing required parameter {key!r}")
    try:
        return float(params[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number") from exc
