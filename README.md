# theater-control

## Overview

A self-hosted, Dockerized web application that provides a single, landscape-optimized control surface for a home theater, replacing the current three-app iPad split-view workflow (Trinnov interface, Roomie Remote, and the MadVR Envy web app). The application runs as a container on the existing Ubuntu/Docker host alongside the Plex and *arr stack, is reachable from any browser on the LAN, and orchestrates every device in the theater through a unified backend. This repository is the framework and specification; the working application is built against it.

The system is organized in two layers: a Python (FastAPI) backend that owns all device communication and orchestration, and a browser-based front end optimized for an 11-inch iPad in landscape. Each device is integrated through a self-contained adapter with a common interface, so devices can be added, replaced, or repaired without touching the rest of the system.

## Prerequisites

1. An Ubuntu host running Docker and Docker Compose (the existing *arr/Plex host is expected).
2. Network reachability from the host to every controlled device. Several devices (Trinnov, MadVR Envy) restrict control to the same subnet, so the container must run with host networking or on the theater VLAN.
3. Static IP addresses or DHCP reservations for every controlled device. Device discovery is out of scope for the initial build.
4. Device-specific prerequisites documented in `docs/devices/` (for example, the JVC network password must be set before IP control is possible).
5. Python 3.11 or later and Node.js 20 or later for local development outside Docker.

## Installation / Setup

1. Clone the repository and check out the `dev` branch.
2. Copy `config/devices.example.yaml` to `config/devices.yaml` and fill in the IP addresses, ports, and credentials for your equipment.
3. Copy `.env.example` to `.env` and populate secrets (JVC password, Hue application key, Plex token). Never commit `.env` or `config/devices.yaml`.
4. Build and start the stack: `docker compose up -d --build`.
5. Open the front end at `http://<host-ip>:8487` on the iPad and add it to the Home Screen for a fullscreen experience.

## Usage

The interface is organized around scenes and per-device panels. The five primary use cases are:

1. Theater On: powers the JVC, applies the correct MadVR profile, waits for the projector to report power, and validates input and latency mode.
2. Theater Off: powers down the JVC and returns devices to standby.
3. Lighting Control: sets Philips Hue scenes and levels.
4. Media Control: an embedded Plex browser/controller and a Kaleidescape transport remote.
5. Trinnov Control: input selection and volume adjustment for the Altitude CI.

Each use case is defined in `docs/usecases/` and implemented as an orchestration routine in `backend/app/orchestration/`.

## Configuration

All device connection details live in `config/devices.yaml`. All secrets live in environment variables loaded from `.env`. See `docs/CONFIGURATION.md` for the full schema, and each file in `docs/devices/` for device-specific settings and prerequisites.

## Local Development

Run the two halves independently without Docker:

Backend:

```
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio          # for the test suite
python -m pytest                            # runs offline, no hardware
uvicorn backend.app.main:app --port 8080    # needs config/devices.yaml and .env
```

Front end (Vite dev server proxies `/api` and `/ws` to the backend on port 8080):

```
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # production bundle in frontend/dist
```

In production the backend serves the built front end from its static mount, so the whole stack is one origin. The tests and the front-end build run without any device on the network.

## Contributing

This repository follows a lightweight GitHub standard for maintainability.

1. Branch from `dev` using `feature/short-description` or `fix/short-description`.
2. Make changes with clear, typed commit messages (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
3. Open a pull request against `dev` with a description of the change, referencing any related issue.
4. Merge only after review approval. `main` holds production-ready code only.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md)

## License

MIT. See [LICENSE](./LICENSE).
