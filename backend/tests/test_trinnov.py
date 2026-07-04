from __future__ import annotations

import pytest

from backend.app.adapters.trinnov import TrinnovAdapter
from backend.tests.fakes import FakeTransport

SOURCES = {"kaleidescape": 0, "plex": 1, "gaming_pc": 3}


def _adapter():
    transport = FakeTransport()
    adapter = TrinnovAdapter("trinnov", "10.0.0.3", sources=SOURCES, transport=transport)
    return adapter, transport


async def test_volume_set_sends_absolute_db():
    adapter, transport = _adapter()
    await adapter.send("volume_set", {"db": -22.5})
    assert transport.sent == ["volume -22.5"]


async def test_volume_adjust_sends_delta():
    adapter, transport = _adapter()
    await adapter.send("volume_adjust", {"delta": -1.0})
    assert transport.sent == ["dvolume -1.0"]


async def test_mute_maps_to_binary():
    adapter, transport = _adapter()
    await adapter.send("mute", {"state": "on"})
    await adapter.send("mute", {"state": "off"})
    assert transport.sent == ["mute 1", "mute 0"]


async def test_source_by_name_resolves_id():
    adapter, transport = _adapter()
    await adapter.send("source", {"name": "gaming_pc"})
    assert transport.sent == ["profile 3"]


async def test_unknown_source_name_raises():
    adapter, _ = _adapter()
    with pytest.raises(ValueError):
        await adapter.send("source", {"name": "nope"})


async def test_power_off_sends_secured_command():
    adapter, transport = _adapter()
    await adapter.send("power", {"state": "off"})
    assert transport.sent == ["power_off_SECURED_FHZMCH48FE"]


async def test_power_on_sends_wol_when_mac_configured(monkeypatch):
    transport = FakeTransport()
    adapter = TrinnovAdapter(
        "trinnov", "10.0.0.3", sources=SOURCES, mac="64-98-9e-01-1b-ff", transport=transport
    )
    sent = {}
    monkeypatch.setattr(
        "backend.app.adapters.trinnov.send_magic_packet",
        lambda mac, *a, **k: sent.setdefault("mac", mac),
    )
    await adapter.send("power", {"state": "on"})
    assert sent["mac"] == "64-98-9e-01-1b-ff"


async def test_power_on_without_mac_raises():
    adapter, _ = _adapter()  # no mac configured
    with pytest.raises(ValueError):
        await adapter.send("power", {"state": "on"})


async def test_inbound_status_updates_state():
    adapter, _ = _adapter()
    adapter._handle_line("Welcome on Trinnov Optimizer (Version 4.3.0, ID 12)")
    adapter._handle_line("VOLUME -30.0")
    adapter._handle_line("MUTE 1")
    adapter._handle_line("CURRENT_PROFILE 1")
    status = await adapter.get_status()
    assert status.extra["volume"] == -30.0
    assert status.extra["mute"] is True
    assert status.input == "plex"  # id 1 maps to friendly name


async def test_registers_on_connect():
    adapter, transport = _adapter()
    await adapter._on_connect()
    assert transport.sent == ["id theater-control"]
