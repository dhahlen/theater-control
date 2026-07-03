# Build Brief for the Implementing Agent

This repository is the framework and specification for a home theater automation suite. Your job is to implement the working application against these specifications. Read this file first, then `docs/ARCHITECTURE.md`, then the relevant `docs/devices/` and `docs/usecases/` files before writing code.

## What this is

A self-hosted, Dockerized web app that runs on the user's Ubuntu host (alongside a Plex and *arr Docker stack) and replaces a three-app iPad split view (Trinnov interface, Roomie Remote, MadVR Envy web app) with one landscape-optimized browser interface on an 11-inch iPad.

## Non-negotiable constraints

1. All device communication lives in the backend. The front end never talks to a device directly and holds no secrets.
2. Every device is integrated behind the common adapter interface in `backend/app/adapters/base.py`. Do not bypass it.
3. The backend container runs with host networking. The Trinnov (port 44100) and MadVR Envy (port 44077) accept control only from the same subnet, and MadVR power-on uses Wake-on-LAN broadcast. Do not move to bridge networking without solving both.
4. Secrets come from environment variables (`.env`), never from the repo or the YAML config. Device connection details come from `config/devices.yaml`.
5. Follow the repository standards below for Git, naming, and tone.

## Build order (recommended)

1. Backend skeleton: config loader + pydantic schema, FastAPI app, in-memory state model, WebSocket, and the `/api` endpoints in `docs/ARCHITECTURE.md`.
2. Adapters, in this priority order, each with a mock transport and unit tests:
   - JVC NZ900 (`docs/devices/jvc-nz900.md`) — protocol proven; you may use the `jvc_projector_python` library directly.
   - Trinnov Altitude CI (`docs/devices/trinnov-altitude.md`) — confirm the volume/source command tokens against the official Trinnov protocol PDF first; transport is confirmed.
   - MadVR Envy (`docs/devices/madvr-envy.md`) — protocol confirmed from the vendor reference source in `docs/devices/reference/EnvyIpControl/`; you may use `py-madvr`. Control the Envy directly over TCP 44077 (decided architecture); the existing Envy-Web app is not part of this build. Remember the mandatory heartbeat and Wake-on-LAN power-on.
   - Philips Hue (`docs/devices/philips-hue.md`) — local bridge REST.
   - Kaleidescape (`docs/devices/kaleidescape.md`) — confirm tokens against the Kaleidescape control protocol manual.
   - Plex (`docs/devices/plex.md`) — embedded Plex Web iframe first; native controller optional.
3. Orchestration routines (`docs/usecases/`): Theater On and Theater Off first (they carry the validation logic), then the panels.
4. Front end: landscape SPA (React + Vite + TypeScript recommended). Status bar, scene buttons with live progress checklist, and per-device panels. Touch targets at least 44x44 points.
5. Docker: complete the `Dockerfile` and `docker-compose.yml`, verify host networking and env loading.
6. Phase 2 stubs only: leave `ac_mx_44x` and `mxnet` as documented stubs. Do not build pool house features yet.

## Verified protocol facts (do not re-derive)

- JVC NZ900: TCP 20554; NZ auth = SHA256 of `<password>` + literal `JVCKWPJ`; Control4 mode must be OFF; commands `power`, `input_mode` (hdmi1/hdmi2), `low_latency` (on/off), `picture_mode`; power-on is asynchronous, poll until `power` reads `on`.
- Trinnov Altitude CI: TCP 44100; same-subnet only; welcome banner on connect; ASCII line protocol; confirm exact volume/source tokens against official docs.
- MadVR Envy: TCP 44077; ASCII commands terminated by `\n`, `OK` ack; periodic `Heartbeat` required or the Envy drops the connection; up to 16 concurrent connections; power-on via Wake-on-LAN (magic packet to UDP port 9, MAC dash-separated); `PowerOff`/`Standby`/`Restart` over IP; `GetMacAddress`, `GetIncomingSignalInfo`, `GetOutgoingSignalInfo`, `GetAspectRatio`, `GetTemperatures`; menu via `KeyPress`/`KeyHold <BUTTON>`. Confirmed from the vendor reference source included at `docs/devices/reference/EnvyIpControl/`. See `docs/devices/madvr-envy.md`.
- Philips Hue: local bridge; app-key auth; `PUT /api/<key>/lights/<id>/state` with `{"on":true,"bri":0-254}`; or CLIP v2 for scenes.
- Plex: PMS HTTP API (`/status/sessions`, `/clients`), remote-control API needs `X-Plex-Client-Identifier` + `X-Plex-Target-Client-Identifier`; embed Plex Web for browse/play.
- Kaleidescape: TCP (port 10000 typical); ASCII colon-delimited, CR-terminated; confirm tokens against the manual.
- AC-MX-44X (phase 2): TCP 23 or RS-232 57600; `GET STA`; routing commands.
- MXNet (phase 2): CBOX Telnet port 24; `config get version`; encoder/decoder routing.

## Definition of done (phase 1)

1. Theater On and Theater Off run end to end against the real devices, with the live progress checklist and the validation rules in the use-case docs (JVC power/input/low-latency are the pass/fail checks).
2. Trinnov panel shows live volume/mute/source and can set them.
3. Lighting panel recalls Hue scenes and sets group level without disturbing the existing play-triggered dimming.
4. Media panel embeds Plex Web and provides a working Kaleidescape transport remote.
5. The whole thing runs from `docker compose up -d --build` and is usable fullscreen in Safari on the iPad in landscape.
6. Adapters have mock-based unit tests; orchestration has sequencing tests against mock adapters.

## Repository standards (apply to all work)

- Git: branch from `dev` (`feature/…`, `fix/…`), PR into `dev`, `main` is production-only. Semantic versioning. Typed commit messages: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, 50-char subject.
- Every meaningful change is its own commit for clean rollback.
- Keep `README.md` and `CHANGELOG.md` current.
- Writing/tone in docs and comments: no em dashes, no "actually" as a corrective, no filler openers, Oxford comma, active voice, spell out acronyms on first use.
- This is a personal project hosted at github.com/dhahlen/theater-control.
