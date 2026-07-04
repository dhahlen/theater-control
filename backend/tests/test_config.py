from __future__ import annotations

import textwrap

import pytest

from backend.app.core.config import ConfigError, load_config, require_secret


def _write(tmp_path, body: str):
    path = tmp_path / "devices.yaml"
    path.write_text(textwrap.dedent(body))
    return path


def test_loads_valid_config(tmp_path, monkeypatch):
    monkeypatch.setenv("JVC_PASSWORD", "secret")
    path = _write(tmp_path, """
        jvc:
          host: "10.0.0.1"
          target_input: "hdmi1"
        madvr:
          host: "10.0.0.2"
          mac: "00:11:22:33:44:55"
        sources:
          plex:
            jvc_input: "hdmi1"
            low_latency: false
        default_source: "plex"
    """)
    cfg = load_config(path)
    assert cfg.jvc.host == "10.0.0.1"
    # MAC is normalized to dash-separated lowercase for Wake-on-LAN.
    assert cfg.madvr.mac == "00-11-22-33-44-55"
    assert cfg.secrets.jvc_password == "secret"
    assert require_secret(cfg, "jvc_password") == "secret"


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "does-not-exist.yaml")


def test_default_source_must_be_known(tmp_path):
    path = _write(tmp_path, """
        sources:
          plex:
            jvc_input: "hdmi1"
        default_source: "kaleidescape"
    """)
    with pytest.raises(ConfigError):
        load_config(path)


def test_invalid_mac_raises(tmp_path):
    path = _write(tmp_path, """
        madvr:
          host: "10.0.0.2"
          mac: "not-a-mac"
    """)
    with pytest.raises(ConfigError):
        load_config(path)


def test_missing_secret_raises(tmp_path):
    path = _write(tmp_path, """
        jvc:
          host: "10.0.0.1"
    """)
    cfg = load_config(path)
    with pytest.raises(ConfigError):
        require_secret(cfg, "jvc_password")


def test_loads_poolhouse_config(tmp_path, monkeypatch):
    monkeypatch.setenv("HUE_POOLHOUSE_APP_KEY", "phkey")
    monkeypatch.setenv("LG_CLIENT_KEY", "lgkey")
    path = _write(tmp_path, """
        plex:
          base_url: "http://10.0.0.20:32400"
        poolhouse:
          trinnov:
            host: "10.0.0.109"
            sources:
              shield: 0
              gaming_pc: 1
          hue:
            bridge_ip: "10.0.0.184"
            zones:
              poolhouse:
                group: "3"
              office:
                group: "1"
                scenes:
                  Dim: "sceneid1"
          lg:
            host: "10.0.0.224"
            mac: "9C:6B:00:01:F1:D1"
            inputs:
              shield: "HDMI_1"
          plex:
            player_id: "abc-android"
            player_name: "Pool House SHIELD"
          default_source: "shield"
    """)
    cfg = load_config(path)
    assert cfg.poolhouse.trinnov.host == "10.0.0.109"
    assert cfg.poolhouse.hue.zones["office"].scenes["Dim"] == "sceneid1"
    assert cfg.poolhouse.lg.mac == "9c-6b-00-01-f1-d1"
    assert cfg.poolhouse.plex.player_id == "abc-android"
    assert cfg.secrets.hue_poolhouse_app_key == "phkey"
    assert cfg.secrets.lg_client_key == "lgkey"
