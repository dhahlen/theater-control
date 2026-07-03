from __future__ import annotations

from backend.app.adapters.jvc import JvcAdapter
from backend.tests.fakes import FakeJvcProjector


async def _adapter(**kwargs):
    proj = FakeJvcProjector(**kwargs)
    adapter = JvcAdapter("jvc", "10.0.0.1", "pw", projector=proj)
    await adapter.connect()
    return adapter, proj


async def test_power_on_command():
    adapter, proj = await _adapter()
    from jvcprojector import command

    await adapter.send("power", {"state": "on"})
    assert await proj.get(command.Power) == "on"


async def test_input_and_low_latency_commands():
    adapter, proj = await _adapter(Power="on")
    from jvcprojector import command

    await adapter.send("input_mode", {"input": "hdmi2"})
    await adapter.send("low_latency", {"state": "on"})
    assert await proj.get(command.Input) == "hdmi2"
    assert await proj.get(command.LowLatencyMode) == "on"


async def test_picture_mode_underscore_maps_to_hyphen():
    adapter, proj = await _adapter(Power="on")
    from jvcprojector import command

    await adapter.send("picture_mode", {"mode": "frame_adapt_hdr"})
    assert await proj.get(command.PictureMode) == "frame-adapt-hdr"


async def test_get_status_when_on_reports_input_and_latency():
    adapter, _ = await _adapter(Power="on", Input="hdmi1", LowLatencyMode="off", Signal="signal")
    status = await adapter.get_status()
    assert status.power == "on"
    assert status.input == "hdmi1"
    assert status.extra["low_latency"] == "off"
    assert status.extra["source_status"] == "signal"


async def test_wait_until_power_polls_through_warmup(monkeypatch):
    # Simulate the asynchronous warm-up: standby -> reserved -> on.
    adapter, _ = await _adapter(power_sequence=["standby", "reserved", "on"])

    async def _instant_sleep(_):
        return None

    monkeypatch.setattr("backend.app.adapters.jvc.asyncio.sleep", _instant_sleep)
    assert await adapter.wait_until_power("on", timeout_s=30) is True


async def test_invalid_param_raises():
    adapter, _ = await _adapter(Power="on")
    import pytest

    with pytest.raises(ValueError):
        await adapter.send("input_mode", {"input": "hdmi9"})
