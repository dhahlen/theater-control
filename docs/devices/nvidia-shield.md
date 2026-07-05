# Nvidia Shield (Android TV) — non-Plex now-playing

Plex playback shows in the Plex/Tautulli card, but streaming apps (Netflix, Prime
Video, Apple TV, YouTube, etc.) do not create a Plex session. To show what is
playing for any app, the Shield is queried directly over ADB on TCP 5555.

## Setup

1. On the Shield: Settings → Device Preferences → About → tap Build several times
   to enable Developer options, then Settings → Device Preferences → Developer
   options → enable **Network debugging** (and note the IP shown).
2. Add the `poolhouse.shield` block to `devices.yaml` with the Shield's host and
   port 5555.
3. Mount a writable volume for the persisted ADB key so the on-screen
   authorization is not repeated after a container restart, e.g. in the compose
   service: `- /opt/theater-control/data:/data`, and set `key_dir: "/data"`.
4. On first connect the Shield shows an "Allow network debugging?" prompt with
   this client's RSA key fingerprint — accept it (and "always allow"). The key is
   stored under `key_dir`.

## What it reads

- `dumpsys media_session` — the active app's package, playback state (playing,
  paused), and title/subtitle metadata.
- `dumpsys activity activities` — the foreground app, mapped to a friendly name
  (Netflix, Prime Video, Apple TV, YouTube, Disney+, Max, Spotify, ...).

The UI shows the Shield's current app and title with transport controls whenever
Plex is not the active source.

## Control

Transport is sent as Android media key events over ADB: play/pause (85), play
(126), pause (127), stop (86), next (87), previous (88), rewind (89), fast
forward (90), plus home (3) and back (4). Apps can be launched by package with
`monkey`.

## Notes

- `dumpsys media_session` output varies by Android/app version; the parser is
  defensive and prefers the playing session. If an app's title does not appear,
  capture its `dumpsys media_session` block so the parser can be adjusted.
- The ADB shell is injected in the adapter, so parsing and command mapping are
  unit-tested without a device.
