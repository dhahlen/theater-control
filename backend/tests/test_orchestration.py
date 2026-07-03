from __future__ import annotations

from backend.app.adapters.base import DeviceStatus, Reachability
from backend.app.orchestration.theater_on import run_theater_on, StepStatus
from backend.app.orchestration.theater_off import run_theater_off

CONFIG = {
    "jvc": {"target_input": "hdmi1", "target_picture_mode": "frame_adapt_hdr"},
    "madvr": {"profiles": {"plex": "1", "gaming_pc": "2"}},
    "trinnov": {"sources": {"plex": 1, "gaming_pc": 3}},
    "sources": {
        "plex": {"jvc_input": "hdmi1", "low_latency": False},
        "gaming_pc": {"jvc_input": "hdmi2", "low_latency": True},
    },
    "theater_off": {"power_off_trinnov": False, "lighting_scene": "bright"},
}


class MockJvc:
    def __init__(self, power="standby", input="hdmi1", low_latency="off"):
        self.device_id = "jvc"
        self._power = power
        self._input = input
        self._low_latency = low_latency
        self.sent: list[tuple[str, dict]] = []

    async def read_power(self):
        return self._power

    async def wait_until_power(self, target, timeout_s=60.0):
        self._power = target
        return True

    async def send(self, command, params=None):
        params = params or {}
        self.sent.append((command, params))
        if command == "power":
            self._power = params["state"]
        elif command == "input_mode":
            self._input = params["input"]
        elif command == "low_latency":
            self._low_latency = params["state"]
        return {}

    async def get_status(self):
        return DeviceStatus(
            device_id="jvc", reachable=Reachability.ONLINE, power=self._power,
            input=self._input, extra={"low_latency": self._low_latency},
        )


class MockTrinnov:
    def __init__(self, source=None):
        self.device_id = "trinnov"
        self._source = source
        self.sent: list[tuple[str, dict]] = []

    async def send(self, command, params=None):
        params = params or {}
        self.sent.append((command, params))
        if command == "source":
            self._source = params.get("name")
        return {}

    async def get_status(self):
        return DeviceStatus(device_id="trinnov", reachable=Reachability.ONLINE,
                            power="on", input=self._source)


class MockMadvr:
    def __init__(self, online=True):
        self.device_id = "madvr"
        self._online = online
        self.sent: list[tuple[str, dict]] = []

    async def send(self, command, params=None):
        self.sent.append((command, params or {}))
        return {}

    async def get_status(self):
        r = Reachability.ONLINE if self._online else Reachability.OFFLINE
        return DeviceStatus(device_id="madvr", reachable=r, power="on")


async def _collect(coro_factory):
    events = []

    async def emit(step):
        events.append((step.step, step.status))

    result = await coro_factory(emit)
    return result, events


async def test_theater_on_success_from_cold():
    jvc, trinnov, madvr = MockJvc(power="standby"), MockTrinnov(), MockMadvr()
    adapters = {"jvc": jvc, "trinnov": trinnov, "madvr": madvr}

    result, events = await _collect(
        lambda emit: run_theater_on("plex", adapters, CONFIG, emit)
    )

    assert result.overall == "success"
    # JVC was powered, input set to hdmi1, low latency off.
    assert ("power", {"state": "on"}) in jvc.sent
    assert ("input_mode", {"input": "hdmi1"}) in jvc.sent
    assert ("low_latency", {"state": "off"}) in jvc.sent
    # Trinnov selected the mapped source.
    assert ("source", {"name": "plex"}) in trinnov.sent


async def test_theater_on_gaming_pc_uses_hdmi2_and_low_latency():
    jvc = MockJvc(power="on")
    adapters = {"jvc": jvc}
    result, _ = await _collect(
        lambda emit: run_theater_on("gaming_pc", adapters, CONFIG, emit)
    )
    assert result.overall in ("success", "partial")
    assert ("input_mode", {"input": "hdmi2"}) in jvc.sent
    assert ("low_latency", {"state": "on"}) in jvc.sent


async def test_theater_on_idempotent_when_already_on():
    jvc = MockJvc(power="on", input="hdmi1", low_latency="off")
    adapters = {"jvc": jvc}
    result, events = await _collect(
        lambda emit: run_theater_on("plex", adapters, CONFIG, emit)
    )
    # Power step should report "ok" without issuing a power command.
    assert ("power", {"state": "on"}) not in jvc.sent
    assert result.overall == "success"


async def test_theater_on_fails_without_jvc():
    result, _ = await _collect(
        lambda emit: run_theater_on("plex", {}, CONFIG, emit)
    )
    assert result.overall == "failed"


async def test_theater_off_success():
    jvc = MockJvc(power="on")

    # After off is sent, read_power should report standby.
    async def read_power():
        return jvc._power

    orig_send = jvc.send

    async def send(command, params=None):
        res = await orig_send(command, params)
        if command == "power" and (params or {}).get("state") == "off":
            jvc._power = "standby"
        return res

    jvc.send = send
    jvc.read_power = read_power

    adapters = {"jvc": jvc, "madvr": MockMadvr()}
    result, events = await _collect(
        lambda emit: run_theater_off(adapters, CONFIG, emit)
    )
    assert result.overall in ("success", "partial")
    assert any(s == "jvc_power_off" and st == StepStatus.OK for s, st in events)


async def test_theater_off_fails_without_jvc():
    result, _ = await _collect(lambda emit: run_theater_off({}, CONFIG, emit))
    assert result.overall == "failed"
