# Device Integration: Trinnov Altitude CI

## Status

Protocol documented and open. Trinnov publishes an open IP control API with discrete On/Off. This adapter is implemented as a raw-socket client against that protocol. A community reference exists at [`binarylogic/trinnov-altitude-homeassistant`](https://github.com/binarylogic/trinnov-altitude-homeassistant).

## Transport

- Protocol: TCP/IP, raw socket, line-oriented ASCII.
- Port: 44100.
- Same-subnet restriction: for security, the Altitude accepts control connections only from a client on the same subnet as the processor. The backend container must therefore run on the theater network (see `docs/ARCHITECTURE.md`, Networking).
- On connect, the Altitude sends a welcome message. The adapter should read and log it, then identify the client.

## Protocol Behavior

1. Open a TCP connection to port 44100.
2. Read the welcome banner.
3. Send an identification command to register the client (per the Trinnov protocol document).
4. Send commands as newline-terminated ASCII strings. The processor emits asynchronous status broadcasts, so the adapter should maintain a persistent connection and parse pushed state rather than polling where possible.

## Required Capabilities (Phase 1)

| Capability | Purpose |
|---|---|
| Power on / off | Discrete on and off commands |
| Volume set (absolute) | Set volume to a specific level for the volume slider |
| Volume adjust (relative) | Step volume up/down |
| Volume read | Report current volume for the UI |
| Mute on/off/read | Mute control and state |
| Input/source select | Switch active source/profile |
| Input read | Report current source for the UI |

## Adapter Requirements

1. Maintain a persistent connection and parse asynchronous state updates so the front end reflects volume, mute, and source changes made from any controller (including the Trinnov's own app or remote).
2. `get_status()` returns power, volume, mute, and current source.
3. Map friendly source names from `config/devices.yaml` to the processor's source identifiers so the UI shows human-readable inputs.
4. Reconnect automatically if the connection drops, with backoff, since this is the most-used panel in the UI.

## Exact Command Syntax (to confirm against the official document)

The precise command tokens (for example, the identification string, volume command name and scale, and source-select syntax) must be confirmed against the official Trinnov IP control protocol PDF and the Home Assistant reference before implementation. The transport facts above (port 44100, same-subnet, welcome banner, ASCII line protocol) are confirmed. Treat the command tokens as the one open item for this device and verify them first.

## Configuration

```yaml
trinnov:
  host: "192.168.x.x"
  port: 44100
  sources:
    # friendly_name: trinnov_source_id
    kaleidescape: 0
    plex: 1
    madvr: 2
    gaming_pc: 3
```

## References

- TCP/IP protocol parameters (port 44100, same-subnet, welcome message): https://mediola.answerbase.com/4576632/Trinnov-Altitude-16
- Trinnov Altitude CI open IP control API (discrete On/Off): https://www.futureland.fr/img/cms/Trinnov/2025/ALTITUDE%20CI/Fiche%20technique%20Trinnov%20AltitudeCI.pdf
- Community reference implementation: https://github.com/binarylogic/trinnov-altitude-homeassistant
- Trinnov downloads (official protocol documents): https://www.trinnov.com/en/resources/downloads/
