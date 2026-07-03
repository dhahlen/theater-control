"""Kaleidescape player adapter.

Protocol: TCP port 10000, line-oriented ASCII, colon-delimited, CR-terminated.
Messages take the form ``<cpdid>/<seq>/<COMMAND>:<args>:`` with the local
component id (default ``01``) and a single-digit sequence (``1`` for requests).
Responses and asynchronous status broadcasts arrive on the same connection with
seq ``!`` for unsolicited events.

Command and status tokens confirmed against the community reference library
``pykaleidescape`` (used by Home Assistant), which mirrors the Kaleidescape
System Control Protocol Reference Manual:
  - transport:  PLAY, PAUSE, STOP, NEXT, PREVIOUS, SCAN_FORWARD, SCAN_REVERSE
  - power:      LEAVE_STANDBY, ENTER_STANDBY
  - navigation: UP, DOWN, LEFT, RIGHT, SELECT, CANCEL, KALEIDESCAPE_MENU_TOGGLE
  - status:     GET_DEVICE_POWER_STATE, GET_PLAY_STATUS, GET_MOVIE_LOCATION,
                GET_PLAYING_TITLE_NAME, plus the matching broadcasts.

See docs/devices/kaleidescape.md. The transport is injected for unit tests.
"""

from __future__ import annotations

import logging
from typing import Any

from ..core.transport import LineTransport
from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.kaleidescape")

KALEIDESCAPE_PORT = 10000

# Named capability -> protocol command token (no arguments).
TRANSPORT_COMMANDS = {
    "play": "PLAY",
    "pause": "PAUSE",
    "stop": "STOP",
    "next": "NEXT",
    "previous": "PREVIOUS",
    "scan_forward": "SCAN_FORWARD",
    "scan_reverse": "SCAN_REVERSE",
    "replay": "REPLAY",
    "up": "UP",
    "down": "DOWN",
    "left": "LEFT",
    "right": "RIGHT",
    "select": "SELECT",
    "cancel": "CANCEL",
    "menu": "KALEIDESCAPE_MENU_TOGGLE",
    "leave_standby": "LEAVE_STANDBY",
    "enter_standby": "ENTER_STANDBY",
}

# Query commands issued by get_status.
STATUS_QUERIES = (
    "GET_DEVICE_POWER_STATE",
    "GET_PLAY_STATUS",
    "GET_MOVIE_LOCATION",
    "GET_PLAYING_TITLE_NAME",
)


class KaleidescapeAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        port: int = KALEIDESCAPE_PORT,
        cpdid: str = "01",
        transport: LineTransport | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._cpdid = cpdid
        self._transport = transport

        self._power: str | None = None
        self._play_status: str | None = None
        self._movie_location: str | None = None
        self._title: str | None = None

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        if self._transport is None:
            self._transport = LineTransport(
                self._host,
                self._port,
                on_line=self._handle_line,
                on_connect=self._on_connect,
                terminator=b"\r",
            )
        await self._transport.start()

    async def disconnect(self) -> None:
        if self._transport is not None:
            await self._transport.stop()

    async def _on_connect(self) -> None:
        # Subscribe to asynchronous status events, then prime current state.
        await self._raw("ENABLE_EVENTS")
        for query in STATUS_QUERIES:
            await self._raw(query)

    # -- inbound parsing --------------------------------------------------

    def _handle_line(self, line: str) -> None:
        # Format: <cpdid>/<seq>/<STATUS>:<field>:<field>:...:<checksum>
        parts = line.split("/", 2)
        if len(parts) < 3:
            return
        body = parts[2]
        name, _, rest = body.partition(":")
        fields = [f for f in rest.split(":") if f != ""]
        if name == "DEVICE_POWER_STATE" and fields:
            # fields[0] == "0"/"1" or "standby"/"on" depending on firmware.
            self._power = "on" if fields[0] in ("1", "on") else "standby"
        elif name == "PLAY_STATUS" and fields:
            self._play_status = fields[0]
        elif name == "MOVIE_LOCATION" and fields:
            self._movie_location = fields[0]
        elif name in ("TITLE_NAME", "PLAYING_TITLE_NAME") and fields:
            self._title = fields[0]

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        connected = bool(self._transport and self._transport.connected)
        if connected:
            for query in STATUS_QUERIES:
                try:
                    await self._raw(query)
                except Exception:
                    break
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE if connected else Reachability.OFFLINE,
            power=self._power if connected else None,
            extra={
                "play_status": self._play_status,
                "movie_location": self._movie_location,
                "title": self._title,
            },
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        token = TRANSPORT_COMMANDS.get(command)
        if token is None:
            raise ValueError(f"unknown kaleidescape command {command!r}")
        await self._raw(token)
        return {"sent": token}

    async def _raw(self, command_token: str) -> None:
        if self._transport is None:
            raise ConnectionError("kaleidescape transport not started")
        # Requests use seq "1"; a trailing colon closes the (empty) argument list.
        await self._transport.send_line(f"{self._cpdid}/1/{command_token}:")

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [Capability(name, {}, name.replace("_", " ")) for name in TRANSPORT_COMMANDS]
