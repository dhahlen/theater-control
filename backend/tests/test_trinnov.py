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


async def test_registers_and_requests_presets_on_connect():
    adapter, transport = _adapter()
    await adapter._on_connect()
    assert transport.sent == ["id theater-control", "get_all_label", "get_current_preset"]


async def test_preset_upmixer_dim_bypass_commands():
    adapter, transport = _adapter()
    await adapter.send("preset", {"index": 9})
    await adapter.send("upmixer", {"mode": "auto"})
    await adapter.send("dim", {"state": "on"})
    await adapter.send("bypass", {"state": "off"})
    assert transport.sent == ["loadp 9", "upmixer auto", "dim 1", "bypass 0"]


async def test_upmixer_validates_mode():
    adapter, _ = _adapter()
    with pytest.raises(ValueError):
        await adapter.send("upmixer", {"mode": "nope"})


async def test_inbound_presets_and_modes():
    adapter, _ = _adapter()
    adapter._handle_line("LABEL 0: Movie Reference")
    adapter._handle_line("LABEL 1: Music")
    adapter._handle_line("CURRENT_PRESET 0")
    adapter._handle_line("UPMIXER auto")
    adapter._handle_line("DIM 1")
    adapter._handle_line("CURRENT_SOURCE_FORMAT_NAME DTS-HD Master Audio")
    status = await adapter.get_status()
    assert status.extra["presets"] == {"0": "Movie Reference", "1": "Music"}
    assert status.extra["current_preset"] == 0
    assert status.extra["upmixer"] == "auto"
    assert status.extra["dim"] is True
    assert status.extra["source_format"] == "DTS-HD Master Audio"
