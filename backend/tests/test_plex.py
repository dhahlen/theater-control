from __future__ import annotations

import pytest

from backend.app.adapters.plex import PlexAdapter

SESSION = {
    "title": "Dune: Part Two",
    "type": "movie",
    "year": 2024,
    "duration": 9960000,
    "viewOffset": 1800000,
    "thumb": "/library/metadata/1234/thumb/1700000000",
    "Player": {"state": "playing", "title": "SHIELD Android TV"},
    "Session": {"bandwidth": 40000},
    "Media": [{
        "bitrate": 61000, "width": 3840, "height": 2160, "videoResolution": "4k",
        "videoCodec": "hevc", "audioCodec": "truehd", "audioChannels": 8,
        "container": "mkv",
        "Part": [{"file": "/movies/Dune Part Two (2024)/Dune.mkv", "size": 45000000000}],
    }],
}


class FakeResponse:
    def __init__(self, payload=None, content=b"", headers=None):
        self._payload = payload or {}
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeHttp:
    def __init__(self, sessions_payload):
        self._sessions = sessions_payload
        self.calls: list[tuple[str, dict]] = []

    async def get(self, url, params=None, headers=None):
        self.calls.append((url, params or {}))
        if url == "/status/sessions":
            return FakeResponse(self._sessions)
        if url == "/photo/:/transcode":
            return FakeResponse(content=b"\x89PNG", headers={"content-type": "image/png"})
        return FakeResponse({})

    async def aclose(self):
        return None


def _adapter(sessions_payload):
    client = FakeHttp(sessions_payload)
    return PlexAdapter("plex", "http://10.0.0.20:32400", "tok", web_url="http://w",
                       client=client), client


async def test_now_playing_extracts_rich_details():
    adapter, _ = _adapter({"MediaContainer": {"size": 1, "Metadata": [SESSION]}})
    status = await adapter.get_status()
    np = status.extra["now_playing"]
    assert np["title"] == "Dune: Part Two"
    assert np["resolution"] == "4k"
    assert np["bitrate"] == 61000
    assert np["video_codec"] == "hevc"
    assert np["audio_channels"] == 8
    assert np["thumb"].startswith("/library/metadata/")
    assert np["file"].endswith("Dune.mkv")
    assert np["transcoding"] is False


EPISODE = {
    "type": "episode", "title": "Home", "grandparentTitle": "The Expanse",
    "parentIndex": 2, "index": 4, "year": 2017, "contentRating": "TV-14",
    "duration": 3600000, "viewOffset": 1643000,
    "Genre": [{"tag": "Drama"}, {"tag": "Sci-Fi"}, {"tag": "Mystery"}, {"tag": "Extra"}],
    "Rating": [
        {"image": "imdb://image.rating", "value": 8.0},
        {"image": "themoviedb://image.rating", "value": 8.0},
        {"image": "rottentomatoes://image.rating.ripe", "value": 8.8},
    ],
    "Media": [{
        "bitrate": 30000, "videoResolution": "4k", "videoCodec": "hevc",
        "audioCodec": "dca", "audioChannels": 6, "container": "mkv",
        "videoFrameRate": "24p",
        "Part": [{"file": "/tv/Expanse/S02E04.mkv", "size": 8000000000,
                  "Stream": [{"streamType": 1, "colorTrc": "smpte2084"}]}],
    }],
}


async def test_now_playing_episode_ratings_genres_hdr():
    adapter, _ = _adapter({"MediaContainer": {"size": 1, "Metadata": [EPISODE]}})
    np = (await adapter.get_status()).extra["now_playing"]
    assert np["episode"] == "S02E04"
    assert np["runtime_min"] == 60
    assert np["genres"] == ["Drama", "Sci-Fi", "Mystery"]      # capped at 3
    assert np["dynamic_range"] == "HDR10"
    assert {"source": "IMDb", "value": 8.0} in np["ratings"]
    assert {"source": "RT", "value": 8.8} in np["ratings"]


async def test_no_sessions_is_none():
    adapter, _ = _adapter({"MediaContainer": {"size": 0}})
    status = await adapter.get_status()
    assert status.extra["now_playing"] is None
    assert status.extra["web_url"] == "http://w"


async def test_fetch_art_proxies_transcode():
    adapter, client = _adapter({"MediaContainer": {}})
    data, ctype = await adapter.fetch_art("/library/metadata/1/thumb/9")
    assert data == b"\x89PNG"
    assert ctype == "image/png"
    assert client.calls[-1][0] == "/photo/:/transcode"


async def test_fetch_art_rejects_external_path():
    adapter, _ = _adapter({"MediaContainer": {}})
    with pytest.raises(ValueError):
        await adapter.fetch_art("http://evil.example/x.png")
