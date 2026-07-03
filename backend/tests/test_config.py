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
