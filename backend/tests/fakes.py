"""Shared test doubles: a fake line transport and a fake JVC projector.

These let the adapters be exercised without any hardware or sockets. The fake
transport records outbound lines and lets a test feed inbound lines straight to
the adapter's line handler.
"""

from __future__ import annotations

from typing import Any


class FakeTransport:
    """Stand-in for core.transport.LineTransport with the same call surface."""

    def __init__(self) -> None:
        self.sent: list[str] = []
        self.connected = True
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True
        self.connected = False

    async def send_line(self, line: str) -> None:
        if not self.connected:
            raise ConnectionError("not connected")
        self.sent.append(line)


class FakeJvcProjector:
    """Minimal stand-in for jvcprojector.JvcProjector.

    Stores state keyed by the library command class, so ``get``/``set`` behave
    like the real projector without a network. ``power_sequence`` lets a test
    simulate the asynchronous warm-up by returning successive power reads.
    """

    def __init__(self, power_sequence: list[str] | None = None, **initial: Any) -> None:
        from jvcprojector import command

        self._c = command
        self._state: dict[Any, str] = {
            command.Power: "standby",
            command.Input: "hdmi1",
            command.LowLatencyMode: "off",
            command.Signal: "none",
        }
        for key, value in initial.items():
            self._state[getattr(command, key)] = value
        self._power_sequence = list(power_sequence or [])
        self.connected = False

    async def connect(self, **_: Any) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def get(self, cls: Any) -> str:
        if cls is self._c.Power and self._power_sequence:
            self._state[cls] = self._power_sequence.pop(0)
        return self._state[cls]

    async def set(self, cls: Any, value: Any = None) -> None:
        self._state[cls] = value
