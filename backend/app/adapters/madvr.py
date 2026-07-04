"""MadVR Envy Extreme adapter.

Protocol confirmed from the vendor reference source at
docs/devices/reference/EnvyIpControl/EnvyIpControlMainForm.pas. See
docs/devices/madvr-envy.md.

Key facts baked in below:
  - TCP port 44077; ASCII commands terminated by "\n"; "OK" is the ack.
  - A periodic "Heartbeat" must be sent or the Envy drops the connection.
  - Power on = Wake-on-LAN magic packet (UDP broadcast, port 9); MAC required.
  - Power off / standby / restart are sent over the IP connection.
  - Menu navigation via KeyPress/KeyHold <BUTTON>.
  - On connect, GetMacAddress caches the MAC for future Wake-on-LAN.

The transport and heartbeat are injected/overridable so the adapter is
unit-testable without an Envy. See tests/test_madvr.py.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..core.transport import LineTransport
from ..core.wol import send_magic_packet
from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.madvr")

MADVR_PORT = 44077
CONNECT_TIMEOUT_S = 2.0
DEFAULT_HEARTBEAT_S = 5

# Remote buttons accepted by KeyPress / KeyHold (from the vendor source).
REMOTE_BUTTONS = [
    "OK", "UP", "DOWN", "LEFT", "RIGHT", "POWER", "INFO", "MENU",
    "SETTINGS", "INPUT", "BACK", "RED", "GREEN", "BLUE", "YELLOW",
    "MAGENTA", "CYAN",
]

# Aspect-ratio modes accepted by SetAspectRatioMode.
ASPECT_MODES = ["Auto", "2.40:1", "2.35:1", "2.20:1", "1.85:1", "16:9", "4:3"]

# Command verbs a profile macro is allowed to send, so a config typo cannot push
# an arbitrary or destructive command at the Envy.
MACRO_VERBS = {"SetAspectRatioMode", "KeyPress", "KeyHold", "RestoreSettings"}

# Query commands and the response keyword each returns.
QUERY_COMMANDS = {
    "GetIncomingSignalInfo": "IncomingSignalInfo",
    "GetOutgoingSignalInfo": "OutgoingSignalInfo",
    "GetAspectRatio": "AspectRatio",
    "GetTemperatures": "Temperatures",
}


class MadvrAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        mac: str,
        port: int = MADVR_PORT,
        heartbeat_seconds: int = DEFAULT_HEARTBEAT_S,
        profile_macros: dict[str, list[str]] | None = None,
        transport: LineTransport | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._mac = mac  # dash-separated, used for WoL
        self._heartbeat_seconds = heartbeat_seconds
        self._profile_macros = dict(profile_macros or {})
        self._transport = transport

        self._signal: dict[str, str] = {}
        self._temperatures: dict[str, int] = {}
        self._heartbeat_task: asyncio.Task[None] | None = None

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        if self._transport is None:
            self._transport = LineTransport(
                self._host,
                self._port,
                on_line=self._handle_line,
                on_connect=self._on_connect,
                terminator=b"\n",
                connect_timeout=CONNECT_TIMEOUT_S,
            )
        await self._transport.start()
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(), name=f"madvr-heartbeat:{self._host}"
            )

    async def disconnect(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        if self._transport is not None:
            await self._transport.stop()

    async def _on_connect(self) -> None:
        # Cache the MAC for Wake-on-LAN on the next cold start.
        await self._transport.send_line("GetMacAddress")

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self._heartbeat_seconds)
            try:
                if self._transport and self._transport.connected:
                    await self._transport.send_line("Heartbeat")
            except Exception as exc:
                log.debug("madvr heartbeat send failed: %s", exc)

    # -- inbound parsing --------------------------------------------------

    def _handle_line(self, line: str) -> None:
        if line == "OK":
            return
        # The Envy echoes KeyPress <BUTTON> back; ignore echoes.
        if line.startswith("KeyPress") or line.startswith("KeyHold"):
            return
        keyword, _, rest = line.partition(" ")
        if keyword == "MacAddress" and rest:
            self._mac = rest.strip().replace(":", "-")
            return
        if keyword == "Temperatures":
            self._temperatures = _parse_temperatures(rest)
            self._signal[keyword] = rest.strip()
            return
        if keyword in QUERY_COMMANDS.values():
            self._signal[keyword] = rest.strip()

    # -- power ------------------------------------------------------------

    async def wake(self) -> None:
        """Power on via Wake-on-LAN magic packet (UDP broadcast, port 9)."""

        if not self._mac:
            raise ValueError("madvr wake requires a configured MAC")
        send_magic_packet(self._mac)

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        connected = bool(self._transport and self._transport.connected)
        if connected:
            # Refresh signal telemetry; responses land via _handle_line.
            for query in QUERY_COMMANDS:
                try:
                    await self._transport.send_line(query)
                except Exception:
                    break
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE if connected else Reachability.OFFLINE,
            power="on" if connected else "standby",
            extra={
                "mac": self._mac,
                "signal": dict(self._signal),
                "temperatures": dict(self._temperatures),
            },
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}

        if command == "wake":
            await self.wake()
            return {"power": "waking"}
        if command == "power_off":
            await self._send_raw("PowerOff")
            return {"power": "off"}
        if command == "standby":
            await self._send_raw("Standby")
            return {"power": "standby"}
        if command == "restart":
            await self._send_raw("Restart")
            return {"power": "restarting"}
        if command in ("key_press", "key_hold"):
            button = params.get("button")
            if button not in REMOTE_BUTTONS:
                raise ValueError(f"button must be one of {REMOTE_BUTTONS}, got {button!r}")
            verb = "KeyPress" if command == "key_press" else "KeyHold"
            await self._send_raw(f"{verb} {button}")
            return {"button": button}
        if command == "set_aspect_ratio_mode":
            mode = params.get("mode")
            if mode not in ASPECT_MODES:
                raise ValueError(f"mode must be one of {ASPECT_MODES}, got {mode!r}")
            await self._send_raw(f"SetAspectRatioMode {mode}")
            return {"aspect_ratio_mode": mode}
        if command == "profile_cycle":
            # This Envy is configured so GREEN cycles the picture profiles.
            await self._send_raw("KeyPress GREEN")
            return {"profile": "cycled"}
        if command == "restore_settings":
            target = params.get("target")
            if not target:
                raise ValueError("restore_settings requires a 'target'")
            await self._send_raw(f"RestoreSettings {target}")
            return {"restored": target}

        raise ValueError(f"unknown madvr command {command!r}")

    async def _send_raw(self, line: str) -> None:
        """Send a raw command line with the trailing newline."""

        if self._transport is None:
            raise ConnectionError("madvr transport not started")
        await self._transport.send_line(line)

    def has_profile_macro(self, source: str) -> bool:
        return bool(self._profile_macros.get(source))

    async def run_profile_macro(self, source: str) -> list[str]:
        """Run the configured profile macro for a source.

        Each entry is a raw Envy command line (verb whitelisted), except the
        pseudo-command ``Delay <ms>`` which pauses client-side to pace a
        multi-step sequence (for example between GREEN profile cycles).
        """

        macro = self._profile_macros.get(source) or []
        executed: list[str] = []
        for line in macro:
            verb, _, rest = line.strip().partition(" ")
            if verb in ("Delay", "Wait"):
                await asyncio.sleep(float(rest) / 1000.0)
                executed.append(line)
                continue
            if verb not in MACRO_VERBS:
                raise ValueError(
                    f"macro command {verb!r} not allowed; permitted: "
                    f"{sorted(MACRO_VERBS)} plus Delay <ms>"
                )
            await self._send_raw(line)
            executed.append(line)
        return executed

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return [
            Capability("wake", {}, "Power on via Wake-on-LAN"),
            Capability("power_off", {}, "Power off over IP (PowerOff)"),
            Capability("standby", {}, "Standby over IP (Standby)"),
            Capability("restart", {}, "Restart over IP (Restart)"),
            Capability("key_press", {"button": REMOTE_BUTTONS}, "Remote key press"),
            Capability("key_hold", {"button": REMOTE_BUTTONS}, "Remote key hold"),
            Capability("set_aspect_ratio_mode", {"mode": ASPECT_MODES}, "Set aspect ratio mode"),
            Capability("profile_cycle", {}, "Cycle picture profile (GREEN)"),
            Capability(
                "restore_settings",
                {"target": ["Installer", "Suggested", *[str(i) for i in range(1, 17)]]},
                "Restore a stored settings slot/profile",
            ),
        ]


# The Envy's GetTemperatures reply is four Celsius integers: GPU, HDMI, CPU,
# mainboard (per the vendor reference and py-madvr).
_TEMP_LABELS = ("gpu", "hdmi", "cpu", "mainboard")


def _parse_temperatures(rest: str) -> dict[str, int]:
    values: list[int] = []
    for token in rest.split():
        try:
            values.append(int(float(token)))
        except ValueError:
            continue
    return {label: value for label, value in zip(_TEMP_LABELS, values)}
