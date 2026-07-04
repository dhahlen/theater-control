# Changelog

All notable changes to this project are documented in this file. This project follows semantic versioning (MAJOR.MINOR.PATCH).

## [Unreleased]

### Changed

- More iPad-fit polish: the dashboard MadVR card is now status-only (the full remote lives on the MadVR tab), fixing the bottom cutoff and keeping the Theater tab from scrolling; the MadVR tab is two columns with a sticky remote that stays put while the rest scrolls; the JVC picture-mode buttons are a proper grid (no overlap); source buttons use real brand logos (Nvidia, ROG, Kaleidescape) with role labels in uniform vertical cards; Kaleidescape is shortened to "Kscape"; and the Theater On/Off buttons are slightly smaller.

- iPad-fit and touch polish: the mute control is now a speaker icon that reflects mute state (fixing the cut-off "Unmute" button on the main screen), the Trinnov source selector uses spacious icon cards instead of bunched buttons, source chips/cards carry per-source marks (Shield, Kaleidescape, PC, HTPC), and the MadVR view is a two-column layout with the remote on the side so the page no longer scrolls on an 11-inch iPad.

### Added

- Multi-tab interface: a top toolbar (Theater, Trinnov, MadVR, JVC, Media, Lighting) with per-device status dots, and full-page device views for granular control. The Trinnov view adds a large volume readout and slider, source/preset/upmixer selectors, and dim/bypass; the MadVR view adds a signal readout, temperature bars, aspect/profile controls, and a full remote.
- Trinnov adapter: preset load (`loadp`), upmixer mode, dim, and bypass commands, plus parsing of preset labels, current preset, upmixer, dim, bypass, sample rate, and source format.
- MadVR adapter: `GetTemperatures` parsed into GPU/HDMI/CPU/mainboard values for the temperature bars.

### Changed

- Plex media panel no longer embeds the full Plex Web app. It shows a rich now-playing card only while something is playing (cover art, ratings, format badges for resolution/HDR/codecs/container/frame rate/bitrate/direct-play, scrub bar, play/pause/stop, and synopsis), and a clean idle state with an optional "Open Plex Web" link otherwise. The adapter now also parses episode label, content rating, runtime, genres, ratings, and HDR dynamic range from `/status/sessions`.

## [0.1.0] - 2026-07-04

First working release: the full phase 1 application (backend, adapters,
orchestration, and the iPad front end), packaged for Docker.

### Added

- Native Plex now-playing card: cover art (proxied server-side so the token never reaches the browser), scrub bar, and quality, bitrate, video/audio codec, container, direct-play-vs-transcode, size, player, and file, parsed from `GET /status/sessions` (`GET /api/plex/art`).
- Trinnov Wake-on-LAN power-on (optional `trinnov.mac`) and a shared MAC normalizer.
- Theater Off can raise the room lights to a level (`theater_off.lighting_level`) when no "lights up" scene exists on the bridge.
- Working FastAPI backend: configuration loader and pydantic schema, in-memory state model, WebSocket event bus, device manager with a background poller, and the REST plus WebSocket API (`backend/app/core/`, `backend/app/api/`, `backend/app/main.py`).
- Device adapters behind the common interface: JVC NZ900 (via `pyjvcprojector`), Trinnov Altitude CI, MadVR Envy, Philips Hue, Kaleidescape, and Plex, plus Phase 2 stubs for the AVPro AC-MX-44X and MXNet (`backend/app/adapters/`).
- Shared transport helpers: a reconnecting line-oriented TCP client and a Wake-on-LAN sender (`backend/app/core/transport.py`, `backend/app/core/wol.py`).
- Theater On and Theater Off orchestration routines with the documented sequencing, idempotency, validation rules, and live progress events (`backend/app/orchestration/`).
- Landscape iPad front end (React, Vite, TypeScript): status bar, Theater On/Off scene buttons with a live progress checklist, and per-device panels for Trinnov, lighting, media (embedded Plex plus a Kaleidescape remote), MadVR, and JVC (`frontend/`).
- Backend unit and integration test suite covering config, every adapter, the orchestration routines, and the API, runnable offline with no hardware (`backend/tests/`).
- Completed multi-stage Dockerfile (builds the front end, serves it from the backend) and a non-secret `GET /api/ui-config` endpoint.
- Vendor authoritative reference source for the MadVR Envy IP control protocol, imported from the official EnvyIpControl sample application (`docs/devices/reference/EnvyIpControl/`).

### Confirmed

- MadVR Envy profile activation resolved (previously the one open item): the adapter runs a per-source macro of raw Envy command lines (`madvr.profile_macros`) with a `Delay <ms>` pseudo-command, covering `SetAspectRatioMode` and `GREEN`-key profile cycling on customized Envys, with fallbacks to stored slots and automatic profiles. Adds `set_aspect_ratio_mode` and `profile_cycle` MadVR commands and controls in the UI.
- Trinnov command and status tokens verified against the community `trinnov-altitude` library: absolute volume (`volume <db>`), relative volume (`dvolume`), mute (`mute 0|1`), source select (`profile <id>`), the `id` registration handshake, and the `VOLUME`/`MUTE`/`CURRENT_PROFILE` broadcasts.
- Kaleidescape command tokens and message framing verified against the `pykaleidescape` library (`<cpdid>/<seq>/<COMMAND>:` frames, CR-terminated).

### Changed

- Rewrote the MadVR Envy integration specification against the vendor source, replacing researched assumptions with confirmed protocol facts (`docs/devices/madvr-envy.md`).
- Updated the implementing-agent build brief with confirmed MadVR facts (`CLAUDE.md`).

### Decided

- MadVR control architecture: the adapter controls the Envy directly over TCP 44077. The existing custom Envy-Web app is not part of this build and no core control path depends on it; it may optionally be embedded as an iframe for advanced menus during transition. Recorded across `docs/devices/madvr-envy.md`, `CLAUDE.md`, and `docs/usecases/media-control.md`.

### Notes

- Confirmed MadVR facts: TCP port 44077, newline-terminated ASCII commands with `OK` acknowledgement, mandatory periodic `Heartbeat` to hold the connection, up to 16 concurrent connections, power-on via Wake-on-LAN magic packet (UDP port 9, dash-separated MAC), and `PowerOff`/`Standby`/`Restart` over IP.
- The per-profile activation token still requires confirmation and is flagged as an open item in the MadVR specification.

## [0.0.1] - 2026-07-03

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
