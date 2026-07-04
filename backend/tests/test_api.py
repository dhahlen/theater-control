from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import AppConfig
from backend.app.main import build_app


@pytest.fixture
def client():
    # An empty config yields a running app with no devices, which is enough to
    # exercise the API surface, state snapshot, and WebSocket.
    app = build_app(AppConfig())
    with TestClient(app) as c:
        yield c


def test_state_snapshot(client):
    resp = client.get("/api/state")
    assert resp.status_code == 200
    assert "devices" in resp.json()


def test_devices_empty(client):
    resp = client.get("/api/devices")
    assert resp.status_code == 200
    assert resp.json() == {"devices": []}


def test_unknown_device_404(client):
    assert client.get("/api/devices/nope").status_code == 404


def test_unknown_scene_404(client):
    assert client.post("/api/scenes/does-not-exist").status_code == 404


def test_websocket_sends_snapshot(client):
    with client.websocket_connect("/ws") as ws:
        message = ws.receive_json()
        assert message["type"] == "snapshot"
        assert "devices" in message["state"]
