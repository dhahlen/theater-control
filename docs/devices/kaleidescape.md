# Device Integration: Kaleidescape Player

## Status

Protocol documented. Kaleidescape uses a well-established ASCII control protocol over TCP, widely implemented by control systems (Control4, Crestron, RTI, Roomie). The adapter is a raw-socket client. Confirm the exact message set against the Kaleidescape System Control Protocol Reference Manual, which is available to integrators.

## Transport

- Protocol: TCP/IP, raw socket, line-oriented ASCII.
- Port: 10000 (the standard Kaleidescape control port). Confirm against the reference manual for the specific player model.
- Messages are ASCII, colon-delimited, carriage-return terminated, in the general form `01/1/<COMMAND>:<args>:` with response and status broadcast messages coming back on the same connection.

## Required Capabilities (Phase 1)

The Media Control use case calls for a transport remote, so the adapter exposes standard movie-player controls:

| Capability | Purpose |
|---|---|
| Play / Pause / Stop | Transport control |
| Fast-forward / Rewind / Scan | Scrubbing |
| Next / Previous chapter | Navigation |
| Menu / Up / Down / Left / Right / Select / Cancel | On-screen navigation |
| Leave standby / Enter standby | Power control |
| Now-playing status | Title, cover art reference, play state, and elapsed/duration for the UI |

## Adapter Requirements

1. Maintain a persistent connection to receive asynchronous now-playing and highlighted-selection status broadcasts.
2. `get_status()` returns play state and, where available, the current title and position.
3. Map the transport controls to the exact protocol tokens from the reference manual.
4. The Kaleidescape can report cover-art identifiers; if practical, surface these so the UI can show the current title. This is a nice-to-have, not required for phase 1.

## Configuration

```yaml
kaleidescape:
  host: "192.168.x.x"
  port: 10000
  device_id: "01"   # confirm against your player
```

## References

- Kaleidescape System Control Protocol Reference Manual (request from Kaleidescape / integrator portal).
- Widely mirrored community implementations exist for Home Assistant and other control platforms; use them to confirm token syntax against the manual.
