"""Configuration loading and validation.

Two sources feed the application:

1. ``config/devices.yaml`` for non-secret device details, validated against the
   pydantic schema in this module.
2. Environment variables (from ``.env``) for secrets.

Both are validated on startup. The application fails fast with a clear error if
anything required is missing. See docs/CONFIGURATION.md.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class JvcConfig(BaseModel):
    host: str
    port: int = 20554
    target_input: str = "hdmi1"
    target_picture_mode: str = "frame_adapt_hdr"


def _normalize_mac(value: str) -> str:
    """Normalize a MAC to dash-separated lowercase, which Wake-on-LAN expects.

    Accepts colon-, dash-, dot-, or no-separator input.
    """

    cleaned = value.replace(":", "").replace("-", "").replace(".", "").strip()
    if len(cleaned) != 12 or not all(c in "0123456789abcdefABCDEF" for c in cleaned):
        raise ValueError(f"invalid MAC address: {value!r}")
    pairs = [cleaned[i : i + 2] for i in range(0, 12, 2)]
    return "-".join(p.lower() for p in pairs)


class TrinnovConfig(BaseModel):
    host: str
    port: int = 44100
    safe_max_volume: float = -20.0
    sources: dict[str, int] = Field(default_factory=dict)
    mac: str | None = None  # optional; enables Wake-on-LAN power-on

    @field_validator("mac")
    @classmethod
    def _validate_mac(cls, value: str | None) -> str | None:
        return _normalize_mac(value) if value else None


class MadvrConfig(BaseModel):
    host: str
    port: int = 44077
    mac: str
    heartbeat_seconds: int = 5
    profiles: dict[str, str] = Field(default_factory=dict)
    # Per-source list of raw Envy command lines run by Theater On to select the
    # picture profile (for example an aspect-ratio mode plus GREEN key cycling).
    # Supports a pseudo-command "Delay <ms>" to pace multi-step sequences.
    profile_macros: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("mac")
    @classmethod
    def _validate_mac(cls, value: str) -> str:
        return _normalize_mac(value)


class KaleidescapeConfig(BaseModel):
    host: str
    port: int = 10000
    device_id: str = "01"


class PlexConfig(BaseModel):
    base_url: str
    web_url: str = ""
    default_player_id: str = ""


class HueConfig(BaseModel):
    bridge_ip: str
    room_group_id: str = "1"
    scenes: dict[str, str] = Field(default_factory=dict)


class SourceBehavior(BaseModel):
    """Source-specific target state applied by the Theater On routine."""

    jvc_input: str = "hdmi1"
    low_latency: bool = False


class TheaterOffConfig(BaseModel):
    power_off_trinnov: bool = False
    lighting_scene: str | None = None       # recall a Hue scene on shutdown, or
    lighting_level: int | None = None        # raise the group to this level (0-254)


class AcMx44xConfig(BaseModel):
    host: str
    port: int = 23
    inputs: dict[str, int] = Field(default_factory=dict)
    outputs: dict[str, int] = Field(default_factory=dict)


class MxnetConfig(BaseModel):
    cbox_host: str
    cbox_port: int = 24
    encoders: dict[str, str] = Field(default_factory=dict)
    decoders: dict[str, str] = Field(default_factory=dict)


class Secrets(BaseModel):
    """Secrets sourced from environment variables, never from YAML."""

    jvc_password: str | None = None
    hue_app_key: str | None = None
    plex_token: str | None = None


class AppConfig(BaseModel):
    """Top-level validated configuration for the whole application."""

    jvc: JvcConfig | None = None
    trinnov: TrinnovConfig | None = None
    madvr: MadvrConfig | None = None
    kaleidescape: KaleidescapeConfig | None = None
    plex: PlexConfig | None = None
    hue: HueConfig | None = None

    sources: dict[str, SourceBehavior] = Field(default_factory=dict)
    default_source: str = "kaleidescape"
    theater_off: TheaterOffConfig = Field(default_factory=TheaterOffConfig)

    # Phase 2, present but ignored by phase 1 orchestration.
    ac_mx_44x: AcMx44xConfig | None = None
    mxnet: MxnetConfig | None = None

    # Populated from the environment, not the YAML file.
    secrets: Secrets = Field(default_factory=Secrets)

    # Runtime knobs (env-overridable).
    bind_host: str = "0.0.0.0"
    port: int = 8080
    poll_interval_s: float = 5.0

    @field_validator("default_source")
    @classmethod
    def _known_default(cls, value: str, info: Any) -> str:
        sources = info.data.get("sources") or {}
        if sources and value not in sources:
            raise ValueError(
                f"default_source {value!r} is not one of the configured sources "
                f"{sorted(sources)}"
            )
        return value


class ConfigError(RuntimeError):
    """Raised when configuration or required secrets are missing or invalid."""


def _load_secrets() -> Secrets:
    return Secrets(
        jvc_password=os.environ.get("JVC_PASSWORD"),
        hue_app_key=os.environ.get("HUE_APP_KEY"),
        plex_token=os.environ.get("PLEX_TOKEN"),
    )


def load_config(path: str | os.PathLike[str] | None = None) -> AppConfig:
    """Load and validate configuration from YAML plus environment secrets.

    Raises ConfigError with a clear message when the file is missing, malformed,
    or fails schema validation, so the application fails fast on startup.
    """

    config_path = Path(path) if path else Path(
        os.environ.get("DEVICES_CONFIG", "config/devices.yaml")
    )
    if not config_path.is_file():
        raise ConfigError(
            f"device config not found at {config_path}. Copy "
            "config/devices.example.yaml to config/devices.yaml and fill it in."
        )

    try:
        raw: dict[str, Any] = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"failed to parse {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path} must contain a YAML mapping at the top level")

    raw["secrets"] = _load_secrets().model_dump()
    _apply_env_overrides(raw)

    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"invalid configuration in {config_path}:\n{exc}") from exc


def _apply_env_overrides(raw: dict[str, Any]) -> None:
    if bind := os.environ.get("APP_BIND_HOST"):
        raw["bind_host"] = bind
    if port := os.environ.get("APP_PORT"):
        raw["port"] = int(port)
    if interval := os.environ.get("APP_POLL_INTERVAL_S"):
        raw["poll_interval_s"] = float(interval)


def require_secret(config: AppConfig, name: str) -> str:
    """Return a required secret or raise ConfigError naming the missing variable."""

    value = getattr(config.secrets, name, None)
    if not value:
        env_name = name.upper()
        raise ConfigError(
            f"required secret {env_name} is missing. Set it in .env "
            "(see .env.example)."
        )
    return value
