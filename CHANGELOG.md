# Changelog

All notable changes to this project are documented in this file. This project follows semantic versioning (MAJOR.MINOR.PATCH).

## [Unreleased]

### Added

- Gaming PC telemetry tab: a read-only Gaming PC device that reads the ASUS ROG machine's sensors from Libre Hardware Monitor's web server (`http://<pc>:8085/data.json`) and shows CPU and GPU temperature, load, and power, plus memory load and every other sensor grouped by hardware. The tab appears when a `gaming_pc` block is configured, and reads offline when the PC is off. No secret is required (the local web server is unauthenticated).

## [0.3.1] - 2026-07-05

### Added

- LG picture-mode control restored: the webOS `setSystemSettings` call that returned "404 no such service or method" over the plain SSAP socket is now delivered through the notification-alert indirection used by aiopylgtv and the webOS remote apps (create an alert whose on-close action targets the luna URI, then close it to fire the call). The Display tab exposes the Filmmaker, Cinema, Vivid, Standard, and Game presets again.
- LG brightness control: the Display tab has a brightness slider that sets the OLED Pixel Brightness (the `backlight` picture setting, 0-100) through the same luna path. It commits on release and, since webOS does not report picture settings back over SSAP, tracks its value optimistically. The adapter's `picture_setting` command also covers `brightness`, `contrast`, and `color`.

## [0.3.0] - 2026-07-05

### Added

- Pool House room, live end to end (Phase 2). The backend registers the second room's devices under `ph_*` ids, reusing the adapter layer for the Trinnov Altitude 16 (`ph_trinnov`), the Office Hue bridge as one adapter per zone (`ph_hue_<zone>`), and the Pool House Plex target (`ph_plex`), plus a new LG G5 webOS adapter (`ph_lg`) over the SSAP WebSocket protocol (pairing with a stored client key, power off over IP and on via Wake-on-LAN, volume, mute). New secrets `HUE_POOLHOUSE_APP_KEY` and `LG_CLIENT_KEY`, plus a `poolhouse` config block. A room switcher in the status bar swaps between Theater and Pool House.
- The Pool House front end drives the real devices: Room On powers the LG and sets the Altitude 16 source, Room Off powers the display off, the Trinnov tab controls volume/source/presets/upmixer live, each Hue zone (Pool House, Bar, Lounge, Office) has live brightness/scenes, and the status bar mirrors the display, source, and volume. The LG stays on HDMI 1 (fed by the Altitude 16), so source switching is on the Trinnov.
- Nvidia Shield now-playing over ADB (`ph_shield`): for non-Plex apps (Netflix, Prime Video, Apple TV, YouTube, etc.) the room's media card shows the foreground app and title with transport controls, read from `dumpsys media_session` and sent as media key events. Needs "Network debugging" on the Shield, a `poolhouse.shield` block, and a mounted `key_dir` for the ADB key.
- Optional Tautulli-powered now-playing detail: when a `tautulli` block and `TAUTULLI_API_KEY` are set, the media card merges product, quality profile, per-stream direct-play/transcode decisions, location, bandwidth, and an ETA (per player) into the card, styled like Tautulli, with the show poster and blurred backdrop.

### Changed

- The Theater and Pool House main tabs are single-pane: the grid fills the viewport and never scrolls; only the device sub-tabs scroll. Both fit an 11-inch iPad in landscape even with the Safari URL bar showing, and the app launches fullscreen from the Home Screen.
- Pool House lighting: sliders drag smoothly and commit on release (no polling stutter), the zone label doubles as an on/off toggle with a status dot, and each shows a live brightness percentage.

### Removed

- LG picture-mode control: this webOS firmware returns "404 no such service or method" for the settings call over the network, so it is set on the TV instead. Power, input, volume, and mute remain.

## [0.2.0] - 2026-07-04

### Added

- Pool House room preview (Phase 2 mockup): a room switcher in the status bar, the title switching to "Pool House Control", and a tabbed interface matching the theater (overview plus Display, Trinnov, Lighting, and Media tabs). The overview carries Room On/Off scenes, the Pool House sources, live volume buttons, and per-zone lighting sliders; the Display tab has the full LG G5 menu (power, HDMI input, picture mode, aspect ratio, energy saving, sound output); the Lighting tab exposes each Hue zone (Pool House, Bar, Lounge, Office). The status bar mirrors the theater readout (display, source, volume). The preview is driven by local state until the Pool House adapters land.
- Fullscreen Home Screen web app on iPad: a web app manifest and mobile-web-app meta tags so the app launches standalone (no Safari address bar) when added to the Home Screen, plus safe-area padding for landscape.
- Multi-tab interface: a top toolbar (Theater, Trinnov, MadVR, JVC, Media, Lighting) with per-device status dots, and full-page device views for granular control. The Trinnov view adds a large volume readout and slider, source/preset/upmixer selectors, and dim/bypass; the MadVR view adds a signal readout, temperature bars, aspect/profile controls, and a full remote.
- Trinnov adapter: preset load (`loadp`), upmixer mode, dim, and bypass commands, plus parsing of preset labels, current preset, upmixer, dim, bypass, sample rate, and source format.
- MadVR adapter: `GetTemperatures` parsed into GPU/HDMI/CPU/mainboard values for the temperature bars.
- Phase 2 planning note for a selectable Pool House room (Trinnov Altitude 16, LG G5, Office Hue bridge, Pool House sources), captured in `docs/usecases/pool-house.md`.

### Changed

- Source buttons are now logo-only and uniform: brand logos (Nvidia, ASUS ROG) render on compact white tiles with no redundant text, sources without a fitting logo show a short text label (Kscape, HTPC), and the dashboard source chips are a symmetric 2x2 grid. The dashboard MadVR card regained its profile-change button.
- More iPad-fit polish: the dashboard MadVR card is now status-only (the full remote lives on the MadVR tab), fixing the bottom cutoff and keeping the Theater tab from scrolling; the MadVR tab is two columns with a sticky remote that stays put while the rest scrolls; the JVC picture-mode buttons are a proper grid (no overlap); source buttons use real brand logos (Nvidia, ROG, Kaleidescape) with role labels in uniform vertical cards; Kaleidescape is shortened to "Kscape"; and the Theater On/Off buttons are slightly smaller.
- The dashboard JVC card drops the HDMI 1 / HDMI 2 buttons (input switching stays on the JVC tab) and surfaces the low-latency toggle, which also keeps the MadVR card below it from being clipped.
- iPad-fit and touch polish: the mute control is now a speaker icon that reflects mute state (fixing the cut-off "Unmute" button on the main screen), the Trinnov source selector uses spacious icon cards instead of bunched buttons, source chips/cards carry per-source marks (Shield, Kaleidescape, PC, HTPC), and the MadVR view is a two-column layout with the remote on the side so the page no longer scrolls on an 11-inch iPad.
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
