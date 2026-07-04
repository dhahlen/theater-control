"""Wake-on-LAN magic packet sender.

Used by the MadVR Envy adapter (and optionally others) to power a device on.
The magic packet is six 0xFF bytes followed by the target MAC repeated 16 times,
broadcast over UDP to port 9. Host networking is required for the broadcast to
reach the device subnet.
"""

from __future__ import annotations

import socket

WOL_PORT = 9


def _mac_to_bytes(mac: str) -> bytes:
    cleaned = mac.replace(":", "").replace("-", "").replace(".", "").strip()
    if len(cleaned) != 12:
        raise ValueError(f"invalid MAC address: {mac!r}")
    return bytes.fromhex(cleaned)


def build_magic_packet(mac: str) -> bytes:
    payload = _mac_to_bytes(mac)
    return b"\xff" * 6 + payload * 16


def send_magic_packet(mac: str, broadcast: str = "255.255.255.255", port: int = WOL_PORT) -> None:
    """Broadcast a Wake-on-LAN magic packet for the given MAC."""

    packet = build_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast, port))
