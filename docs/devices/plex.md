# Device Integration: Plex

## Status

Two integration paths, both HTTP. Plex Media Server (PMS) exposes an HTTP API, and Plex players advertise a remote-control (companion) API. The adapter uses the PMS HTTP API for browsing/library and the companion protocol for controlling playback on a player.

## Environment

- Plex Media Server runs on Ubuntu on the same host/network as the *arr Docker stack.
- Authentication uses a Plex token (`X-Plex-Token`) supplied via the `PLEX_TOKEN` environment variable.

## Integration Approach

The Media Control use case wants an embedded Plex browser/controller. There are two complementary layers:

1. Embedded Plex Web: the simplest browser/controller is to embed the Plex Web app (served by PMS) in an iframe panel. This gives full browse-and-play with zero custom UI. Use this as the baseline for phase 1.
2. Native controller (optional, richer): use the PMS HTTP API to list libraries and now-playing sessions (`GET /status/sessions`), and the Plex companion/remote-control API to drive a target player (play, pause, seek, navigation). The remote-control API requires `X-Plex-Client-Identifier` and `X-Plex-Target-Client-Identifier` headers, and players advertise capabilities such as `timeline,playback,navigation,mirror,playqueues` on their companion port (for example 32467).

## Required Capabilities (Phase 1)

| Capability | Path |
|---|---|
| Embedded browse/play | iframe to Plex Web served by PMS |
| Now-playing / active sessions | PMS `GET /status/sessions` |
| Transport control on a player | Plex remote-control API (playback: play, pause, stop, seek) |
| Player list / discovery | PMS `GET /clients` or myPlex resources |

## Adapter Requirements

1. Provide the PMS base URL and token from config/env; expose now-playing sessions for the status bar.
2. For phase 1, the primary deliverable is the embedded Plex Web panel; the native controller endpoints are optional enhancements.
3. Do not embed the Plex token in front-end URLs. If the embedded Plex Web app needs auth, rely on Plex's own session rather than passing the token through the front end.

## Lighting Tie-In

The user already dims Philips Hue when Plex starts playing, via an *arr app or webhook. Keep that existing automation as the source of truth for play-triggered dimming, and expose Hue scene control in this app for manual override (see `docs/devices/philips-hue.md` and `docs/usecases/lighting-control.md`). Optionally, the backend can subscribe to Plex webhooks to reflect play state in the UI, but it should not fight the existing dimming automation.

## Configuration

```yaml
plex:
  base_url: "http://192.168.x.x:32400"
  web_url: "http://192.168.x.x:32400/web"   # for the embedded iframe panel
  # token is provided via the PLEX_TOKEN environment variable
  default_player_id: ""   # optional: client identifier of the theater's Plex player
```

## References

- Plex remote-control (companion) API, headers and capabilities: https://github.com/plexinc/plex-media-player/wiki/Remote-control-API
- PMS HTTP API endpoints (`/status/sessions`, `/clients`) are documented across the Plex API community references.
