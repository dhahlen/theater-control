from __future__ import annotations

from backend.app.core.config import (
    AppConfig,
    HueZoneConfig,
    LgConfig,
    PlexConfig,
    PoolHouseConfig,
    PoolHouseHueConfig,
    PoolHousePlexConfig,
    TrinnovConfig,
)
from backend.app.core.events import EventBus
from backend.app.core.manager import DeviceManager
from backend.app.core.state import StateStore


def _manager(config: AppConfig) -> DeviceManager:
    return DeviceManager(config, StateStore(), EventBus())


def test_poolhouse_adapters_registered():
    config = AppConfig(
        plex=PlexConfig(base_url="http://10.0.0.20:32400"),
        poolhouse=PoolHouseConfig(
            trinnov=TrinnovConfig(host="10.0.0.109", sources={"shield": 0}),
            hue=PoolHouseHueConfig(
                bridge_ip="10.0.0.184",
                zones={
                    "poolhouse": HueZoneConfig(group="3"),
                    "office": HueZoneConfig(group="1", scenes={"Dim": "sid"}),
                },
            ),
            lg=LgConfig(host="10.0.0.224", inputs={"shield": "HDMI_1"}),
            plex=PoolHousePlexConfig(player_id="abc-android"),
        ),
    )
    ids = set(_manager(config).adapters)
    assert {"ph_trinnov", "ph_hue_poolhouse", "ph_hue_office", "ph_lg", "ph_plex"} <= ids


def test_no_poolhouse_no_ph_adapters():
    ids = set(_manager(AppConfig()).adapters)
    assert not any(i.startswith("ph_") for i in ids)
