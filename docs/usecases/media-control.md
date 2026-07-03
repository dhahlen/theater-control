# Use Case: Media Control

## Intent

Browse and control media without leaving the app. This covers an embedded Plex browser/controller, a Kaleidescape transport remote, and access to the MadVR menu.

## Components

1. Plex panel: an embedded Plex Web app (iframe to the PMS web URL) for full browse-and-play. Optionally augmented with a native now-playing readout from the PMS `GET /status/sessions` endpoint and transport control through the Plex remote-control API. See `docs/devices/plex.md`.
2. Kaleidescape remote: a transport remote (play, pause, stop, scan, chapter, menu navigation, standby) driven by the Kaleidescape adapter, with a now-playing readout where available. See `docs/devices/kaleidescape.md`.
3. MadVR menu: menu navigation controls (menu, arrows, OK, back) and profile display, rendered natively and driven by the MadVR adapter over the direct connection. This is the primary and only required MadVR control path. The existing custom Envy-Web app may optionally be embedded as an iframe panel for advanced menus during transition, but no core control depends on it. See `docs/devices/madvr-envy.md`.

## Embedded Panel Guidance

- Embedded third-party web UIs (Plex Web, Envy-Web) are shown in iframes sized for landscape.
- Do not pass secrets through the front end. Rely on the embedded app's own session/auth.
- Native controls (Kaleidescape transport, MadVR menu) are rendered by this app and call the backend API, so they work even where an embedded UI is not available.

## Source Awareness

- The active source (from Theater On) determines which media panel is foregrounded by default: Kaleidescape source foregrounds the Kaleidescape remote; Plex source foregrounds the Plex panel. The user can switch panels at any time.
