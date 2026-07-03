# Configuration

The application reads two sources of configuration: a YAML file for non-secret device details, and environment variables for secrets. Both are validated on startup, and the application fails fast with a clear message if anything required is missing.

## Files

1. `config/devices.yaml` — device connection details, friendly names, input/source maps, scenes, and use-case options. Copy from `config/devices.example.yaml`. Not committed.
2. `.env` — secrets only. Copy from `.env.example`. Not committed.

## Secrets (`.env`)

| Variable | Purpose |
|---|---|
| `JVC_PASSWORD` | Plaintext JVC network password. The JVC adapter hashes it (SHA256 of password + `JVCKWPJ`) internally. |
| `HUE_APP_KEY` | Philips Hue bridge application key. |
| `PLEX_TOKEN` | Plex `X-Plex-Token` for PMS API access. |
| `APP_BIND_HOST` | Optional. Interface for the backend to bind (default `0.0.0.0`). |
| `APP_PORT` | Optional. Backend port (default `8080`). |

## Networking Requirement

The Trinnov and MadVR Envy accept control only from the same subnet, and MadVR power-on uses Wake-on-LAN broadcast. Run the backend container with `network_mode: host`, or attach it to the theater VLAN with a routable address on the device subnet. This is mandatory, not optional.

## Startup Validation

On startup the backend:

1. Loads and validates `config/devices.yaml` against the pydantic schema.
2. Confirms all required environment variables are present.
3. Attempts a non-blocking health check per device and reports reachability, but does not refuse to start if a device is temporarily offline (the interface degrades gracefully).

## Phasing in Config

Phase 2 devices (`ac_mx_44x`, `mxnet`) may be present in `devices.yaml` but are ignored by phase 1 orchestration. Their adapters are stubbed. See `docs/ARCHITECTURE.md`, Phasing.
