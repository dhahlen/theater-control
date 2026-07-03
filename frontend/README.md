# Frontend

Landscape-first single-page application for an 11-inch iPad in Safari. React + Vite + TypeScript is recommended (see `CLAUDE.md` and `docs/ARCHITECTURE.md`), but the front end is decoupled and framework-agnostic.

## Responsibilities

1. Persistent status bar: theater power, active source, Trinnov volume.
2. Scene buttons (Theater On, Theater Off, lighting scenes) that call the orchestration endpoints and render the live progress checklist from the WebSocket.
3. Per-device panels: Trinnov (input + volume), Plex (embedded), Kaleidescape (transport remote), MadVR (menu/profile), lighting (Hue), JVC status/diagnostics.

## Rules

1. No device logic and no secrets in the front end.
2. Read state from `GET /api/state`, subscribe to `WS /ws`, issue intent via the REST endpoints.
3. Touch targets at least 44 by 44 points; layout designed for roughly 1194 by 834 CSS points in landscape.

The build output must land in `dist/` for the Dockerfile's static mount.
