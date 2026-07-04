from __future__ import annotations

import pytest

from backend.app.adapters.kaleidescape import KaleidescapeAdapter
from backend.tests.fakes import FakeTransport


def _adapter():
    transport = FakeTransport()
    adapter = KaleidescapeAdapter("kaleidescape", "10.0.0.5", transport=transport)
    return adapter, transport


async def test_transport_commands_are_framed():
    adapter, transport = _adapter()
    await adapter.send("play", {})
    await adapter.send("pause", {})
    await adapter.send("menu", {})
    assert transport.sent == ["01/1/PLAY:", "01/1/PAUSE:", "01/1/KALEIDESCAPE_MENU_TOGGLE:"]


async def test_unknown_command_raises():
    adapter, _ = _adapter()
    with pytest.raises(ValueError):
        await adapter.send("eject", {})


async def test_handle_line_parses_status():
    adapter, _ = _adapter()
    adapter._handle_line("01/1/DEVICE_POWER_STATE:1:")
    adapter._handle_line("01/!/PLAY_STATUS:playing:2:0:")
    adapter._handle_line("01/!/TITLE_NAME:Blade Runner:")
    status = await adapter.get_status()
    assert status.power == "on"
    assert status.extra["play_status"] == "playing"
    assert status.extra["title"] == "Blade Runner"


async def test_enables_events_on_connect():
    adapter, transport = _adapter()
    await adapter._on_connect()
    assert transport.sent[0] == "01/1/ENABLE_EVENTS:"
