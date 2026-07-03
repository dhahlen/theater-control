# System Architecture

This document defines the architecture for the theater automation suite. It is the authoritative reference for how the system is structured. Device-level detail lives in `docs/devices/`, and use-case behavior lives in `docs/usecases/`.

## Goals and Constraints

1. One browser-based control surface replaces the current three-app iPad split view (Trinnov interface, Roomie Remote, MadVR Envy web app).
2. The application runs as a Docker container on the existing Ubuntu host, next to Plex and the *arr stack.
3. The front end targets an 11-inch iPad in landscape and must work in Safari with no App Store dependency.
4. All device communication is owned by the backend. The front end never talks to a device directly, so credentials and raw protocols stay server-side.
5. Devices are integrated behind a common adapter interface so any single device can be added, replaced, or repaired in isolation.
6. Several devices restrict control to the same subnet (Trinnov, MadVR Envy), which constrains container networking (see Networking).
7. The build must be inexpensive to develop and iterate on with an external coding agent, and every change must be tracked in Git per the repository standard.

## High-Level Layers

The system has four layers, from the device outward to the iPad.

1. Device Adapters: one module per device, each translating a common internal interface into that device's native protocol (TCP, HTTP, Telnet, or Wake-on-LAN). Adapters own connection handling, retries, and status parsing.
2. Orchestration: routines that coordinate multiple adapters to execute a use case (for example, Theater On), including sequencing, waiting for state, and validation.
3. Backend API and State: a FastAPI service that exposes REST endpoints and a WebSocket for live state, holds the in-memory device state model, and serves the front end.
4. Front End: a browser application, landscape-first, presenting scenes and per-device panels, driven entirely by the backend API and WebSocket.

```
+-------------------------------------------------------------+
|                     iPad (Safari, landscape)                |
|            Front End: scenes + per-device panels            |
+---------------------------|---------------------------------+
                            |  REST + WebSocket (LAN, HTTP)
+---------------------------v---------------------------------+
|                  Backend (FastAPI, Docker)                  |
|  API + WebSocket  |  State model  |  Orchestration routines |
+---------------------------|---------------------------------+
                            |  common adapter interface
+---------------------------v---------------------------------+
|  Adapters: JVC | Trinnov | MadVR | Kaleidescape | Plex |    |
|            Hue | AC-MX-44X | MXNet                          |
+---------------------------|---------------------------------+
                            |  native protocols on the LAN
+---------------------------v---------------------------------+
|          Physical devices on the theater network            |
+-------------------------------------------------------------+
```

## Component Responsibilities

### Device Adapters (`backend/app/adapters/`)

Every adapter implements the same base interface (defined in `backend/app/adapters/base.py`) so orchestration and the API treat all devices uniformly. The base contract is:

1. `connect()` and `disconnect()`: establish and tear down the transport, including any handshake or authentication.
2. `get_status()`: return a normalized status object (power, input, and device-specific fields) without side effects.
3. `send(command, params)`: execute a named capability with validated parameters.
4. `capabilities()`: declare the commands the device supports, so the API and front end can render controls dynamically.
5. `health()`: report reachability and last-known connection state for the dashboard.

Adapters never import from the API or front end. They depend only on `core` utilities (logging, config, transport helpers). This keeps each device replaceable and independently testable with a mock transport.

### Orchestration (`backend/app/orchestration/`)

Orchestration routines are the only place multiple devices are coordinated. Each routine is a named, idempotent async function that:

1. Reads target state from configuration and current state from adapters.
2. Issues commands in a defined order with explicit waits (for example, poll JVC power until `on` before validating input).
3. Validates the end state and returns a structured result (success, partial, or failed) with per-step detail.
4. Emits progress events over the WebSocket so the front end can show a live checklist.

Routines must be safe to re-run. If the theater is already on, Theater On verifies and corrects rather than blindly re-sending. See `docs/usecases/` for the step-by-step definition of each routine.

### Backend API and State (`backend/app/api/`, `backend/app/core/`)

The backend exposes:

1. `GET /api/devices` and `GET /api/devices/{id}` for device status and capabilities.
2. `POST /api/devices/{id}/command` to send a single device command.
3. `POST /api/scenes/{name}` to run an orchestration routine (for example, `theater-on`).
4. `GET /api/state` for a full snapshot and `WS /ws` for live updates.

State is held in an in-memory model that is the single source of truth for the front end. A background poller refreshes device status on a configurable interval and pushes deltas over the WebSocket. Persistence beyond runtime state is not required for the initial build; configuration is file-based.

### Front End (`frontend/`)

The front end is a single-page application optimized for landscape on an 11-inch iPad (roughly 1194 by 834 CSS points). It renders:

1. A persistent status bar (theater power, active source, Trinnov volume).
2. Scene buttons that call the orchestration endpoints and display the live progress checklist.
3. Per-device panels: Trinnov (input and volume), Plex (embedded browser/controller), Kaleidescape (transport remote), MadVR (profile and menu), lighting (Hue scenes), and a JVC status/diagnostics panel.

The front end holds no device logic and no secrets. It reads state from `GET /api/state`, subscribes to `WS /ws`, and issues intent through the REST endpoints.

## Recommended Technology Stack

1. Backend: Python 3.11+, FastAPI, Uvicorn, `asyncio` for concurrent device I/O, `pydantic` for config and command validation, `PyYAML` for device config.
2. Device libraries where mature and permissively licensed: `jvc_projector_python` and `py-madvr` are known-good references (MIT, by iloveicedgreentea) and may be used directly or as protocol references. Trinnov, Kaleidescape, AC-MX-44X, and MXNet are implemented as raw-socket adapters against the documented protocols in `docs/devices/`.
3. Front end: a lightweight SPA. React with Vite and TypeScript is recommended for maintainability, though the front end is intentionally decoupled so any framework works. Use CSS designed for landscape and touch targets of at least 44 by 44 points.
4. Packaging: two containers via Docker Compose (backend, front end) or a single container serving both. Prefer a single image for the initial build to simplify deployment.

## Networking

Because the Trinnov and MadVR Envy accept control connections only from the same subnet, the backend container must sit on the theater network with the devices. Use Docker host networking (`network_mode: host`) or place the container on the theater VLAN with a routable address. Document the chosen approach in `docs/CONFIGURATION.md`. Wake-on-LAN for the MadVR Envy requires that broadcast packets reach the device subnet, which host networking satisfies.

## Configuration and Secrets

1. Device connection details (IP, port, model, friendly names, input maps) live in `config/devices.yaml`, validated against a pydantic schema on startup.
2. Secrets (JVC network password, Hue application key, Plex token) live in environment variables from `.env`, never in the repository.
3. The application fails fast on startup with a clear error if required configuration or secrets are missing.

## Error Handling and Safety

1. Every adapter command has a timeout. A hung device must never block the event loop or an orchestration routine.
2. Orchestration routines return partial-failure detail so the front end can show which step failed and offer a retry.
3. Commands that change physical state (projector power) are logged with timestamp, requester, and result.
4. The system degrades gracefully: if one device is unreachable, the rest of the interface remains usable.

## Testing Strategy

1. Each adapter ships with a mock transport and unit tests that assert correct command encoding and status parsing, so most logic is testable without hardware.
2. Orchestration routines are tested against mock adapters to verify sequencing, waits, and validation logic.
3. A small set of integration checks run against real hardware on the theater network, gated behind an environment flag so they never run in continuous integration.

## Phasing

- Phase 1 (this framework): main theater only. JVC NZ900, Trinnov Altitude CI, MadVR Envy Extreme, Kaleidescape, Plex, and Philips Hue, plus the five primary use cases.
- Phase 2 (documented, not built): pool house room (Trinnov Altitude 16, LG G5 display), AC-MX-44X matrix switching for moving the gaming PC between the theater and the pool house display, and MXNet distribution. Adapter stubs and device notes for the AC-MX-44X and MXNet are included so phase 2 slots into the same architecture without rework.
- Home Assistant is available on the network but is not a dependency. It may later be integrated as an additional adapter or as an event source, but the system does not require it.
