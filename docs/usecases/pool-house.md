# Use Case: Pool House Control (Phase 2, planned)

This captures the Pool House room so it slots into the existing architecture in
Phase 2. It is not built yet. The intent is a second room, selectable from the
same app, that reuses the adapter and orchestration layers with a different
device set.

## Room switching

Add a dynamic room selector. When the Pool House room is active:

- The top toolbar title changes from "Theater Control" to "Pool House Control".
- Only the Pool House devices appear: Plex, the Trinnov Altitude 16, and the
  Pool House lighting. The main theater devices (JVC, MadVR Envy, theater
  Trinnov CI) are hidden.
- Scenes (Room On / Room Off) target the Pool House device set.

The single-room theater build stays the default; the room selector is additive.

## Devices

| Device | Detail |
|---|---|
| Display | LG G5 84" at `172.16.17.224` |
| Audio processor | Trinnov Altitude 16 at `172.16.17.109` (distinct from the theater Altitude CI) |
| Streamer | Nvidia Shield (Pool House) at `172.16.17.105` |
| Lighting | Hue Bridge in the Office at `172.16.17.184` (needs its own app key and scene ids in `.env`/config) |
| Plex | same Plex Media Server as the theater |

## Trinnov Altitude 16 inputs (Pool House)

| Input | Source |
|---|---|
| 1 | Nvidia Shield (Pool House) |
| 2 | Gaming PC |
| 3 | Nintendo Switch 2 |
| 4 | Nintendo Switch 1 |
| 5-8 | unused |
| (other) | Bluesound Node 2i |

## Notes / open items

- The Trinnov adapter already supports the Altitude line; a second instance with
  its own host and source map covers the Altitude 16. Confirm the Altitude 16
  source/profile indices are also 0-based on the live unit.
- The LG G5 needs a display adapter (webOS / LG IP control) — new for Phase 2.
- The Nintendo Switch and Bluesound Node 2i are passive HDMI/audio sources
  (Trinnov input selection only); no dedicated control adapter is required for
  the first pass.
- Pool House Hue is a separate bridge, so it needs its own `HUE_APP_KEY` and
  scene ids, gathered separately from the theater bridge.
- The AC-MX-44X matrix (already documented for Phase 2) is what moves the Gaming
  PC between the theater and the Pool House display.
