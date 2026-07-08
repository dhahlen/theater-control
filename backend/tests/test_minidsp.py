from __future__ import annotations

import pytest

from backend.app.adapters.minidsp import MiniDspAdapter

STATUS = {
    "master": {"preset": 0, "source": "Toslink", "volume": -27.0, "mute": False},
    "available_sources": ["analog", "toslink", "usb"],
    "input_levels": [-28.0, -28.1],
    "output_levels": [-57.1, -60.7, -120.0, -120.0],
}


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class FakeClient:
    def __init__(self, payload: object = STATUS) -> None:
        self._payload = payload
        self.posts: list[tuple[str, dict]] = []
        self.gets: list[str] = []

    async def get(self, path: str) -> FakeResponse:
        self.gets.append(path)
        return FakeResponse(self._payload)

    async def post(self, path: str, json: dict) -> FakeResponse:  # noqa: A002
        self.posts.append((path, json))
        return FakeResponse({"ok": True})

    async def aclose(self) -> None:
        return None


class FailingClient:
    async def get(self, path: str):  # noqa: ANN201
        raise ConnectionError("refused")

    async def aclose(self) -> None:
        return None


def _adapter(client: FakeClient | None = None) -> MiniDspAdapter:
    return MiniDspAdapter(
        "minidsp",
        outputs={"front_row": 0, "rear_row": 1},
        presets=["Deep", "Full"],
        client=client or FakeClient(),
    )


async def test_status_reports_master_and_outputs():
    adapter = _adapter()
    status = await adapter.get_status()
    assert status.reachable.value == "online"
    assert status.extra["volume"] == -27.0
    assert status.extra["mute"] is False
    assert status.extra["output_levels"] == [-57.1, -60.7, -120.0, -120.0]
    assert status.extra["outputs"] == {"front_row": 0, "rear_row": 1}
    assert status.extra["preset"] == 0
    assert status.extra["presets"] == ["Deep", "Full"]


async def test_preset_switches_config():
    client = FakeClient()
    adapter = _adapter(client)
    await adapter.send("preset", {"index": 2})
    assert client.posts[-1] == ("/devices/0/config", {"master_status": {"preset": 2}})


async def test_volume_set_clamps_and_posts_master():
    client = FakeClient()
    adapter = _adapter(client)
    await adapter.send("volume_set", {"db": -25})
    assert client.posts[-1] == ("/devices/0/config", {"master_status": {"volume": -25.0}})
    # Below the configured floor clamps to master_min (-80 default).
    await adapter.send("volume_set", {"db": -200})
    assert client.posts[-1][1] == {"master_status": {"volume": -80.0}}


async def test_volume_adjust_uses_cached_base():
    client = FakeClient()
    adapter = _adapter(client)
    await adapter.get_status()  # caches -27.0
    await adapter.send("volume_adjust", {"delta": -3})
    assert client.posts[-1][1] == {"master_status": {"volume": -30.0}}


async def test_master_mute():
    client = FakeClient()
    adapter = _adapter(client)
    await adapter.send("mute", {"state": "on"})
    assert client.posts[-1][1] == {"master_status": {"mute": True}}


async def test_output_gain_by_name_and_index():
    client = FakeClient()
    adapter = _adapter(client)
    await adapter.send("output_gain", {"name": "rear_row", "db": -12})
    assert client.posts[-1] == ("/devices/0/config", {"outputs": [{"index": 1, "gain": -12.0}]})
    await adapter.send("output_gain", {"index": 0, "db": -100})  # clamps to output_min (-40)
    assert client.posts[-1][1] == {"outputs": [{"index": 0, "gain": -40.0}]}


async def test_output_mute_turns_row_off_and_reflects_in_status():
    client = FakeClient()
    adapter = _adapter(client)
    await adapter.send("output_mute", {"name": "front_row", "state": "on"})
    assert client.posts[-1][1] == {"outputs": [{"index": 0, "mute": True}]}
    status = await adapter.get_status()
    # The optimistic per-output mute is echoed back keyed by name.
    assert status.extra["output_mute"]["front_row"] is True
    assert status.extra["output_mute"]["rear_row"] is False


async def test_unknown_output_and_command_raise():
    adapter = _adapter()
    with pytest.raises(ValueError):
        await adapter.send("output_gain", {"name": "middle", "db": -5})
    with pytest.raises(ValueError):
        await adapter.send("nope")


async def test_offline_when_daemon_unreachable():
    adapter = MiniDspAdapter("minidsp", client=FailingClient())
    status = await adapter.get_status()
    assert status.reachable.value == "offline"
