from __future__ import annotations

import asyncio
import json

import pytest

from backend.app.adapters.lg import LgAdapter


class FakeSsap:
    """In-memory SSAP WebSocket: answers register + request messages by id."""

    def __init__(self, client_key: str = "KEY123") -> None:
        self.sent: list[dict] = []
        self._client_key = client_key
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self.closed = False

    async def connect(self) -> None:
        return None

    async def send(self, message: str) -> None:
        msg = json.loads(message)
        self.sent.append(msg)
        mid = msg.get("id")
        mtype = msg.get("type")
        uri = msg.get("uri", "")
        if mtype == "register":
            reply = {"type": "registered", "id": mid, "payload": {"client-key": self._client_key}}
        elif uri.endswith("audio/getVolume"):
            reply = {"type": "response", "id": mid, "payload": {"volume": 12, "muted": False}}
        elif uri.endswith("getForegroundAppInfo"):
            reply = {"type": "response", "id": mid, "payload": {"appId": "com.webos.app.hdmi2"}}
        else:
            reply = {"type": "response", "id": mid, "payload": {"returnValue": True}}
        await self._queue.put(json.dumps(reply))

    async def recv(self) -> str:
        return await self._queue.get()

    async def close(self) -> None:
        self.closed = True


async def _connected(**kwargs):
    fake = FakeSsap()
    adapter = LgAdapter(
        "ph_lg", "10.0.0.9", inputs={"shield": "HDMI_1", "gaming_pc": "HDMI_2"},
        transport_factory=lambda: fake, **kwargs,
    )
    await adapter.connect()
    return adapter, fake


def _uris(fake: FakeSsap) -> list[str]:
    return [m.get("uri") for m in fake.sent if m.get("type") == "request"]


async def test_register_captures_client_key():
    captured = {}
    adapter, fake = await _connected(on_client_key=lambda k: captured.__setitem__("key", k))
    assert adapter._client_key == "KEY123"  # noqa: SLF001
    assert captured["key"] == "KEY123"
    reg = [m for m in fake.sent if m["type"] == "register"][0]
    assert reg["payload"]["manifest"]["permissions"]
    await adapter.disconnect()


async def test_power_off_sends_turnoff():
    adapter, fake = await _connected()
    await adapter.send("power", {"state": "off"})
    assert "ssap://system/turnOff" in _uris(fake)
    await adapter.disconnect()


async def test_power_on_requires_mac():
    adapter, _ = await _connected()
    with pytest.raises(ValueError):
        await adapter.send("power", {"state": "on"})
    await adapter.disconnect()


async def test_volume_set_and_mute():
    adapter, fake = await _connected()
    await adapter.send("volume_set", {"volume": 20})
    await adapter.send("mute", {"state": "on"})
    setvol = [m for m in fake.sent if m.get("uri", "").endswith("audio/setVolume")][0]
    assert setvol["payload"] == {"volume": 20}
    setmute = [m for m in fake.sent if m.get("uri", "").endswith("audio/setMute")][0]
    assert setmute["payload"] == {"mute": True}
    await adapter.disconnect()


async def test_volume_adjust_steps():
    adapter, fake = await _connected()
    await adapter.send("volume_adjust", {"delta": 3})
    ups = [u for u in _uris(fake) if u.endswith("audio/volumeUp")]
    assert len(ups) == 3
    await adapter.disconnect()


async def test_input_by_name():
    adapter, fake = await _connected()
    await adapter.send("input", {"name": "gaming_pc"})
    switch = [m for m in fake.sent if m.get("uri", "").endswith("tv/switchInput")][0]
    assert switch["payload"] == {"inputId": "HDMI_2"}
    with pytest.raises(ValueError):
        await adapter.send("input", {"name": "nope"})
    await adapter.disconnect()


async def test_picture_mode_maps_token():
    adapter, fake = await _connected()
    await adapter.send("picture_mode", {"mode": "Filmmaker"})
    setp = [m for m in fake.sent if m.get("uri", "").endswith("setSystemSettings")][0]
    assert setp["payload"]["settings"]["pictureMode"] == "filmMaker"
    with pytest.raises(ValueError):
        await adapter.send("picture_mode", {"mode": "Bogus"})
    await adapter.disconnect()


async def test_status_reports_volume_and_input():
    adapter, _ = await _connected()
    status = await adapter.get_status()
    assert status.reachable.value == "online"
    assert status.extra["volume"] == 12
    assert status.extra["mute"] is False
    assert status.input == "com.webos.app.hdmi2"
    await adapter.disconnect()


class FailingSsap(FakeSsap):
    """Simulates a TV that is off: the WebSocket never connects."""

    async def connect(self) -> None:
        raise ConnectionError("connection refused")


async def test_status_offline_when_tv_unreachable():
    adapter = LgAdapter("ph_lg", "10.0.0.9", transport_factory=lambda: FailingSsap())
    status = await adapter.get_status()
    assert status.reachable.value == "offline"


async def test_status_autoconnects_and_recovers():
    # A TV that is off at startup, then reachable, should come online on the next
    # poll without a restart.
    states = {"up": False}

    def factory():
        return FakeSsap() if states["up"] else FailingSsap()

    adapter = LgAdapter("ph_lg", "10.0.0.9", transport_factory=factory)
    assert (await adapter.get_status()).reachable.value == "offline"
    states["up"] = True
    assert (await adapter.get_status()).reachable.value == "online"
    await adapter.disconnect()
