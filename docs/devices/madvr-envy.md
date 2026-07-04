# Device Integration: MadVR Envy Extreme

## Status

Protocol confirmed from the official madVR Labs reference implementation. The vendor's "Envy IP Control" sample utility (Delphi source) is included in this repo at `docs/devices/reference/EnvyIpControl/` and is the authoritative source for the wire protocol below. Every command and behavior here was read directly from that source (`EnvyIpControlMainForm.pas`). A mature MIT-licensed Python reference also exists: [`iloveicedgreentea/py-madvr`](https://github.com/iloveicedgreentea/py-madvr).

## Transport

- Protocol: TCP/IP, raw socket.
- Port: 44077.
- Connection timeout in the reference: 2 seconds.
- Commands are ASCII strings terminated by a single line feed (`\n`, 0x0A).
- Responses arrive line-oriented. The Envy may send `\r\n`; normalize to `\n`. A bare `OK` line is the acknowledgement for most commands.
- Up to 16 concurrent client connections are supported, so this adapter can coexist with the existing Envy-Web app and other integrations.
- Same-subnet: as with the Trinnov, control is expected on the local subnet; the backend container is already on the theater network.

## Keepalive (required)

The Envy closes the connection if it does not receive periodic traffic. The reference sends `Heartbeat\n` on a timer. The adapter must send `Heartbeat` at a regular interval (well under any idle timeout) and treat the resulting `OK` as noise. Failing to heartbeat is the most common cause of dropped connections.

## Power

- Power on: Wake-on-LAN. The reference builds a standard magic packet (six `0xFF` bytes followed by the six-byte MAC repeated 16 times) and broadcasts it via UDP to port 9, across the `.255` broadcast addresses of the device subnet. The MAC must be configured. Host networking is required so the broadcast reaches the device subnet.
- Get MAC automatically: on connect, the reference sends `GetMacAddress\n`; the Envy replies `MacAddress <mac>`. The adapter can capture and cache the MAC this way, then use it for Wake-on-LAN on the next cold start.
- Power off (over IP): `PowerOff\n`.
- Standby (over IP): `Standby\n`.
- Restart (over IP): `Restart\n`.

## Confirmed Command Set (from the reference source)

All commands are sent with a trailing `\n`. Arguments shown in angle brackets.

| Purpose | Command | Notes |
|---|---|---|
| Keepalive | `Heartbeat` | Send periodically; expect `OK`. |
| Get MAC (for WoL) | `GetMacAddress` | Response `MacAddress <mac>`. |
| Power off | `PowerOff` | |
| Standby | `Standby` | |
| Restart | `Restart` | |
| Incoming signal info | `GetIncomingSignalInfo` | Resolution, HDR, etc. for status. |
| Outgoing signal info | `GetOutgoingSignalInfo` | What the Envy sends to the JVC. |
| Aspect ratio | `GetAspectRatio` | Detected aspect ratio. |
| Temperatures | `GetTemperatures` | Thermal telemetry. |
| Remote key press | `KeyPress <BUTTON>` | Momentary press. |
| Remote key hold | `KeyHold <BUTTON>` | Press-and-hold (auto-repeat handled client-side). |
| Set aspect ratio mode | `SetAspectRatioMode <mode>` | For example `Auto`, `2.40:1`, `16:9`. Deterministic. |
| Enumerate 3DLUTs | `Enum3DLUTFiles` | Streams `3DLUTFile ...` lines, ends with `3DLUTFile.`. |
| Store settings (named) | `StoreSettings Installer "<name>" "<password>"` | Also `Suggested`, or `StoreSettings <slot 1-16> "<name>"`. |
| Restore settings | `RestoreSettings Installer` | Also `Suggested` or `<slot 1-16>`. |
| Send raw command | `<any text>` | The reference has a passthrough box; any documented Envy command can be sent verbatim. |

### Remote Buttons (for `KeyPress` / `KeyHold`)

`OK`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `POWER`, `INFO`, `MENU`, `SETTINGS`, `INPUT`, `BACK`, `RED`, `GREEN`, `BLUE`, `YELLOW`, `MAGENTA`, `CYAN`.

The Envy echoes `KeyPress <BUTTON>` back on the connection; the reference filters these echoes out of its log.

## Applying a Picture Profile for a Source

The Envy's own profile mechanism is what activates the correct picture settings per source. In the reference utility there is no single "activate profile N" button; profiles are driven either by the Envy's automatic profile rules (based on incoming signal) or by navigating with the remote keys. For the Theater On routine, choose one of these approaches and record the decision in `config/devices.yaml`:

1. Recommended: rely on the Envy's built-in automatic profiles keyed to the incoming signal, so switching the source is enough. The adapter simply confirms the Envy is powered and reports signal state.
2. Explicit: use a stored settings slot or a `KeyPress` menu macro to force a specific profile. If you use stored slots, map `source -> slot` in config and issue `RestoreSettings <slot>`. Confirm the exact profile-activation command against the full Envy IP Control reference guide (the reference sample covers settings slots and remote keys; per-profile activation may use a documented command available in the newest firmware).

Treat the exact per-profile activation token as the one item to confirm against the current Envy IP Control reference guide. Everything else above is confirmed from the vendor source.

### Resolved: per-source profile via a configurable macro

Confirmed against this installation's Envy and its customized IP Control source: there is no single "activate profile N" token here. The `GREEN` remote key is configured to cycle the three picture profiles, and `SetAspectRatioMode <mode>` sets the aspect deterministically. To support both without hard-coding one site's layout, the adapter runs a per-source macro from `config/devices.yaml` (`madvr.profile_macros`): an ordered list of raw Envy command lines, plus a `Delay <ms>` pseudo-command to pace multi-step sequences (for example between `KeyPress GREEN` cycles). Allowed macro verbs are `SetAspectRatioMode`, `KeyPress`, `KeyHold`, and `RestoreSettings`. When no macro is configured, the routine falls back to a stored settings slot, then to the Envy's automatic signal-driven profiles. Because `GREEN` cycling is state-dependent, prefer `SetAspectRatioMode` for deterministic results and confirm the cycle position before relying on a fixed number of `GREEN` presses.

## Adapter Requirements

1. Maintain a persistent connection and a heartbeat timer.
2. On connect, issue `GetMacAddress` and cache the MAC for Wake-on-LAN.
3. Implement power on (WoL), `PowerOff`, `Standby`, and `Restart`.
4. Expose menu navigation via `KeyPress`/`KeyHold` for the Media Control panel.
5. `get_status()` returns reachability, and where available incoming/outgoing signal info and aspect ratio parsed from the query responses.
6. Provide the source-to-profile behavior chosen above for the Theater On routine.

## Control Strategy (Decided): Direct to Envy

This adapter controls the Envy directly over TCP 44077. This is the confirmed architecture, not an option to evaluate. Because the Envy supports up to 16 concurrent connections, the direct connection coexists with the existing custom Envy-Web app and any other integrations without conflict.

Rationale: the direct connection keeps all device logic and state inside the backend adapter layer, gives the panel a single consistent control surface, and removes the dependency on the separate Envy-Web container for core functions (power, signal state, menu navigation, profile confirmation).

Envy-Web is not part of this build. It may remain running independently on the Docker host during the transition, and the panel may optionally surface it as an embedded iframe for advanced or rarely-used menus, but no core control path depends on it. Do not route power, signal, or profile control through Envy-Web.

## Configuration

```yaml
madvr:
  host: "192.168.x.x"
  port: 44077
  mac: "00-11-22-33-44-55"     # dash-separated as in the reference; required for Wake-on-LAN
  heartbeat_seconds: 5
  profile_mode: "auto"         # "auto" (Envy rules) or "slot"
  profiles:                    # only used when profile_mode == "slot"
    kaleidescape: 1
    plex: 1
    gaming_pc: 2
```

## References

- Vendor reference source (authoritative, in this repo): `docs/devices/reference/EnvyIpControl/EnvyIpControlMainForm.pas`
- Official IP Control document (port 44077, 16 concurrent connections): https://madvrenvy.com/wp-content/uploads/EnvyIpControl.pdf
- Python reference library: https://github.com/iloveicedgreentea/py-madvr
