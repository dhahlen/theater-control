from __future__ import annotations

import pytest

from backend.app.adapters.hue import HueAdapter

SCENES = {"movie": "sceneAAA", "bright": "sceneBBB"}


class FakeResponse:
    def __init__(self, payload=None):
        self._payload = payload or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeHttp:
    def __init__(self, get_payload=None):
        self.puts: list[tuple[str, dict]] = []
        self._get_payload = get_payload or {}

    async def put(self, url, json=None):
        self.puts.append((url, json))
        return FakeResponse()

    async def get(self, url):
        return FakeResponse(self._get_payload)

    async def aclose(self):
        return None


def _adapter(get_payload=None):
    client = FakeHttp(get_payload)
    adapter = HueAdapter("hue", "10.0.0.6", "appkey", room_group_id="2", scenes=SCENES, client=client)
    return adapter, client


async def test_recall_scene_sends_scene_id():
    adapter, client = _adapter()
    await adapter.send("recall_scene", {"scene": "movie"})
    url, body = client.puts[0]
    assert url == "/api/appkey/groups/2/action"
    assert body == {"scene": "sceneAAA"}


async def test_set_level_bounds_checked():
    adapter, client = _adapter()
    await adapter.send("set_level", {"bri": 128})
    assert client.puts[0][1] == {"on": True, "bri": 128}
    with pytest.raises(ValueError):
        await adapter.send("set_level", {"bri": 999})


async def test_toggle():
    adapter, client = _adapter()
    await adapter.send("toggle", {"state": "off"})
    assert client.puts[0][1] == {"on": False}


async def test_get_status_reads_group():
    adapter, _ = _adapter(get_payload={"state": {"any_on": True, "all_on": False},
                                       "action": {"bri": 200}})
    status = await adapter.get_status()
    assert status.power == "on"
    assert status.extra["bri"] == 200


async def test_unknown_scene_raises():
    adapter, _ = _adapter()
    with pytest.raises(ValueError):
        await adapter.send("recall_scene", {"scene": "nope"})
