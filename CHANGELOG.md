# Changelog

All notable changes to this project are documented in this file. This project follows semantic versioning (MAJOR.MINOR.PATCH).

## [Unreleased]

### Added

- Vendor authoritative reference source for the MadVR Envy IP control protocol, imported from the official EnvyIpControl sample application (`docs/devices/reference/EnvyIpControl/`).
- MadVR Envy adapter scaffold with confirmed command set (`backend/app/adapters/madvr.py`).

### Changed

- Rewrote the MadVR Envy integration specification against the vendor source, replacing researched assumptions with confirmed protocol facts (`docs/devices/madvr-envy.md`).
- Updated the implementing-agent build brief with confirmed MadVR facts (`CLAUDE.md`).

### Decided

- MadVR control architecture: the adapter controls the Envy directly over TCP 44077. The existing custom Envy-Web app is not part of this build and no core control path depends on it; it may optionally be embedded as an iframe for advanced menus during transition. Recorded across `docs/devices/madvr-envy.md`, `CLAUDE.md`, and `docs/usecases/media-control.md`.

### Notes

- Confirmed MadVR facts: TCP port 44077, newline-terminated ASCII commands with `OK` acknowledgement, mandatory periodic `Heartbeat` to hold the connection, up to 16 concurrent connections, power-on via Wake-on-LAN magic packet (UDP port 9, dash-separated MAC), and `PowerOff`/`Standby`/`Restart` over IP.
- The per-profile activation token still requires confirmation and is flagged as an open item in the MadVR specification.

## [0.1.0] - 2026-07-03

### Added

- Initial framework and specification for the theater automation suite.
- System architecture document defining the backend, adapter, orchestration, and front-end layers (`docs/ARCHITECTURE.md`).
- Per-device integration specifications for the JVC NZ900, Trinnov Altitude CI, MadVR Envy Extreme, Kaleidescape player, Plex, Philips Hue, AVPro AC-MX-44X, and AVPro MXNet (`docs/devices/`).
- Use-case orchestration specifications for Theater On, Theater Off, Lighting Control, Media Control, and Trinnov Control (`docs/usecases/`).
- Configuration schema and example files (`docs/CONFIGURATION.md`, `config/devices.example.yaml`, `.env.example`).
- Build brief for the implementing agent (`CLAUDE.md`).
- Repository scaffold with backend and front-end directory structure, Docker Compose skeleton, and placeholder adapter interfaces.

### Notes

- This release is documentation and scaffold only. No working control code is implemented yet.
- Pool house room (Trinnov Altitude 16, LG G5, AC-MX-44X gaming PC switching) is scoped as phase 2 and documented as such.
