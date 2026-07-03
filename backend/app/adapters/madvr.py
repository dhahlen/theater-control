"""MadVR Envy Extreme adapter (scaffold).

Protocol confirmed from the vendor reference source at
docs/devices/reference/EnvyIpControl/EnvyIpControlMainForm.pas. See
docs/devices/madvr-envy.md.

Key facts baked in below:
  - TCP port 44077; ASCII commands terminated by "\n"; "OK" is the ack.
  - A periodic "Heartbeat" must be sent or the Envy drops the connection.
  - Power on = Wake-on-LAN magic packet (UDP broadcast, port 9); MAC required.
  - Power off / standby / restart are sent over the IP connection.
  - Menu navigation via KeyPress/KeyHold <BUTTON>.

The implementing agent fills in the transport; the command surface is fixed.
"""

from __future__ import annotations

from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus

MADVR_PORT = 44077
CONNECT_TIMEOUT_S = 2
DEFAULT_HEARTBEAT_S = 5

# Remote buttons accepted by KeyPress / KeyHold (from the vendor source).
REMOTE_BUTTONS = [
    "OK", "UP", "DOWN", "LEFT", "RIGHT", "POWER", "INFO", "MENU",
    "SETTINGS", "INPUT", "BACK", "RED", "GREEN", "BLUE", "YELLOW",
    "MAGENTA", "CYAN",
]

# Query commands (each returns a text line to parse for status).
QUERY_COMMANDS = [
    "GetIncomingSignalInfo",
    "GetOutgoingSignalInfo",
    "GetAspectRatio",
    "GetTemperatures",
    "GetMacAddress",
]


class MadvrAdapter(DeviceAdapter):
    def __init__(self, device_id: str, host: str, mac: str,
                 port: int = MADVR_PORT,
                 heartbeat_seconds: int = DEFAULT_HEARTBEAT_S) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._mac = mac                      # dash-separated, used for WoL
        self._heartbeat_seconds = heartbeat_seconds

    async def connect(self) -> None:
        # Open TCP socket to port 44077, start the heartbeat loop, and issue
        # GetMacAddress to cache the MAC for future Wake-on-LAN.
        raise NotImplementedError

    async def disconnect(self) -> None:
        raise NotImplementedError

    async def wake(self) -> None:
        """Power on via Wake-on-LAN magic packet (UDP broadcast, port 9)."""
        raise NotImplementedError

    async def get_status(self) -> DeviceStatus:
        # Parse GetIncomingSignalInfo / GetOutgoingSignalInfo / GetAspectRatio
        # into extra{}. Reachability from connection state.
        raise NotImplementedError

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        # Named capabilities map to raw commands:
        #   power_off -> "PowerOff", standby -> "Standby", restart -> "Restart"
        #   key_press -> "KeyPress <BUTTON>", key_hold -> "KeyHold <BUTTON>"
        #   restore_settings -> "RestoreSettings <slot|Installer|Suggested>"
        # All commands are terminated with "\n"; expect "OK".
        raise NotImplementedError

    async def _send_raw(self, line: str) -> None:
        """Send a raw command line with the trailing newline. Passthrough."""
        raise NotImplementedError

    def capabilities(self) -> list[Capability]:
        return [
            Capability("power_off", {}, "Power off over IP (PowerOff)"),
            Capability("standby", {}, "Standby over IP (Standby)"),
            Capability("restart", {}, "Restart over IP (Restart)"),
            Capability("wake", {}, "Power on via Wake-on-LAN"),
            Capability("key_press", {"button": REMOTE_BUTTONS}, "Remote key press"),
            Capability("key_hold", {"button": REMOTE_BUTTONS}, "Remote key hold"),
            Capability("restore_settings",
                       {"target": ["Installer", "Suggested", "1", "2", "3", "4",
                                   "5", "6", "7", "8", "9", "10", "11", "12",
                                   "13", "14", "15", "16"]},
                       "Restore a stored settings slot/profile"),
        ]
