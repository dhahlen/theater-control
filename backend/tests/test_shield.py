from __future__ import annotations

import pytest

from backend.app.adapters.shield import ShieldAdapter, _parse_foreground, _parse_media_session

NETFLIX_MEDIA = """
Sessions Stack Info:
  Media button session is null
  com.netflix.mediaclient (userId=10):
    package=com.netflix.mediaclient
    state=PlaybackState {state=3, position=120000, speed=1.0}
    metadata: size=3, description=The Crown, S5:E1 Queen Victoria, null
"""

PAUSED_MEDIA = """
  package=com.spotify.tv.android
   state=PlaybackState {state=2, position=1000}
   metadata: size=2, description=Bohemian Rhapsody, Queen, A Night at the Opera
"""

FOCUS = "mResumedActivity: ActivityRecord{7f3 u0 com.netflix.mediaclient/.ui.launch.LaunchActivity t42}"


class RecordingShell:
    def __init__(self, media="", focus=""):
        self.calls: list[str] = []
        self._media = media
        self._focus = focus

    async def __call__(self, command: str) -> str:
        self.calls.append(command)
        if "media_session" in command:
            return self._media
        if "activities" in command:
            return self._focus
        return ""


def test_parse_media_session_playing():
    s = _parse_media_session(NETFLIX_MEDIA)
    assert s["package"] == "com.netflix.mediaclient"
    assert s["state"] == "playing"
    assert s["title"] == "The Crown"
    assert s["subtitle"] == "S5:E1 Queen Victoria"


def test_parse_media_session_paused_drops_null():
    s = _parse_media_session(PAUSED_MEDIA)
    assert s["state"] == "paused"
    assert s["title"] == "Bohemian Rhapsody"
    assert s["subtitle"] == "Queen"


def test_parse_media_session_prefers_playing():
    combined = PAUSED_MEDIA + NETFLIX_MEDIA
    assert _parse_media_session(combined)["package"] == "com.netflix.mediaclient"


def test_parse_media_session_none():
    assert _parse_media_session("no sessions here") is None


def test_parse_foreground():
    assert _parse_foreground(FOCUS) == "com.netflix.mediaclient"


async def test_status_maps_app_name():
    shell = RecordingShell(media=NETFLIX_MEDIA, focus=FOCUS)
    adapter = ShieldAdapter("ph_shield", "10.0.0.5", shell=shell)
    status = await adapter.get_status()
    assert status.reachable.value == "online"
    assert status.extra["app_name"] == "Netflix"
    assert status.extra["state"] == "playing"
    assert status.input == "Netflix"


async def test_transport_sends_keyevent():
    shell = RecordingShell()
    adapter = ShieldAdapter("ph_shield", "10.0.0.5", shell=shell)
    await adapter.send("play_pause")
    assert "input keyevent 85" in shell.calls
    await adapter.send("stop")
    assert "input keyevent 86" in shell.calls
    with pytest.raises(ValueError):
        await adapter.send("nope")


async def test_launch_requires_package():
    shell = RecordingShell()
    adapter = ShieldAdapter("ph_shield", "10.0.0.5", shell=shell)
    await adapter.send("launch", {"package": "com.netflix.mediaclient"})
    assert any("monkey -p com.netflix.mediaclient" in c for c in shell.calls)
    with pytest.raises(ValueError):
        await adapter.send("launch", {})
