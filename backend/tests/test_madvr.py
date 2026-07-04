from __future__ import annotations

import pytest

from backend.app.adapters.madvr import MadvrAdapter
from backend.tests.fakes import FakeTransport

MAC = "00-11-22-33-44-55"


def _adapter():
    transport = FakeTransport()
    adapter = MadvrAdapter("madvr", "10.0.0.4", mac=MAC, transport=transport)
    return adapter, transport


async def test_power_commands_over_ip():
    adapter, transport = _adapter()
    await adapter.send("power_off", {})
    await adapter.send("standby", {})
    await adapter.send("restart", {})
    assert transport.sent == ["PowerOff", "Standby", "Restart"]


async def test_key_press_validates_button():
    adapter, transport = _adapter()
    await adapter.send("key_press", {"button": "MENU"})
    assert transport.sent == ["KeyPress MENU"]
    with pytest.raises(ValueError):
        await adapter.send("key_press", {"button": "BOGUS"})


async def test_wake_sends_magic_packet(monkeypatch):
    adapter, _ = _adapter()
    sent = {}

    def _fake_wol(mac, *a, **k):
        sent["mac"] = mac

    monkeypatch.setattr("backend.app.adapters.madvr.send_magic_packet", _fake_wol)
    await adapter.send("wake", {})
    assert sent["mac"] == MAC


async def test_handle_line_caches_mac_and_signal():
    adapter, _ = _adapter()
    adapter._handle_line("MacAddress AA:BB:CC:DD:EE:FF")
    adapter._handle_line("IncomingSignalInfo 3840x2160 60p HDR")
    adapter._handle_line("KeyPress OK")  # echo, ignored
    adapter._handle_line("OK")           # ack, ignored
    status = await adapter.get_status()
    assert status.extra["mac"] == "AA-BB-CC-DD-EE-FF"
    assert status.extra["signal"]["IncomingSignalInfo"] == "3840x2160 60p HDR"


async def test_get_status_queries_signal():
    adapter, transport = _adapter()
    await adapter.get_status()
    assert "GetIncomingSignalInfo" in transport.sent


async def test_set_aspect_ratio_mode():
    adapter, transport = _adapter()
    await adapter.send("set_aspect_ratio_mode", {"mode": "2.40:1"})
    assert transport.sent == ["SetAspectRatioMode 2.40:1"]
    with pytest.raises(ValueError):
        await adapter.send("set_aspect_ratio_mode", {"mode": "banana"})


async def test_profile_cycle_presses_green():
    adapter, transport = _adapter()
    await adapter.send("profile_cycle", {})
    assert transport.sent == ["KeyPress GREEN"]


async def test_profile_macro_runs_lines_and_delay(monkeypatch):
    transport = FakeTransport()
    macro = {"movie": ["SetAspectRatioMode 2.40:1", "Delay 200", "KeyPress GREEN"]}
    adapter = MadvrAdapter("madvr", "10.0.0.4", mac=MAC, profile_macros=macro,
                           transport=transport)
    slept = {}
    async def _sleep(sec):
        slept["sec"] = sec
    monkeypatch.setattr("backend.app.adapters.madvr.asyncio.sleep", _sleep)

    assert adapter.has_profile_macro("movie") is True
    executed = await adapter.run_profile_macro("movie")
    assert transport.sent == ["SetAspectRatioMode 2.40:1", "KeyPress GREEN"]
    assert slept["sec"] == 0.2
    assert executed == ["SetAspectRatioMode 2.40:1", "Delay 200", "KeyPress GREEN"]


async def test_profile_macro_rejects_unlisted_verb():
    transport = FakeTransport()
    adapter = MadvrAdapter("madvr", "10.0.0.4", mac=MAC,
                           profile_macros={"x": ["PowerOff"]}, transport=transport)
    with pytest.raises(ValueError):
        await adapter.run_profile_macro("x")
    assert transport.sent == []
