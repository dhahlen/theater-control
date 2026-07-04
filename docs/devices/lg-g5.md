# LG G5 (webOS) — Pool House display

The Pool House display is an LG G5 84 inch, controlled over the LG "SSAP"
protocol: a JSON message bus over a WebSocket on `wss://<tv>:3001` (TLS with a
self-signed certificate) or the legacy `ws://<tv>:3000` (plaintext). webOS 2023
and newer require the secure port, so the adapter defaults to 3001 and uses
`wss` for it (certificate verification disabled for the self-signed cert); set
`port: 3000` for older sets that still accept plaintext.

## Pairing

On the first connection the client sends a `register` request with a manifest of
the permissions it needs. The TV shows an on-screen prompt; once accepted it
returns a `client-key`. Store that key in `LG_CLIENT_KEY` (`.env`) so later
connections skip the prompt. Leave `LG_CLIENT_KEY` blank for the first run,
accept the prompt on the TV, then copy the key the adapter logs.

The display must be powered on and reachable for pairing. Enable "LG Connect
Apps" (or "Mobile TV On") in the TV network settings so the SSAP socket is
available.

## Control

Each command is a request with a unique id; the TV replies with a message
carrying the same id. Commands used:

- Power off: `ssap://system/turnOff`
- Volume: `ssap://audio/setVolume` `{"volume": 0-100}`, `ssap://audio/volumeUp`,
  `ssap://audio/volumeDown`
- Mute: `ssap://audio/setMute` `{"mute": bool}`
- Input: `ssap://tv/switchInput` `{"inputId": "HDMI_1"}`
- Picture mode: `ssap://com.webos.service.settings/setSystemSettings`
  `{"category": "picture", "settings": {"pictureMode": "<token>"}}`, where the
  UI names map to the webOS tokens `filmMaker`, `cinema`, `vivid`, `normal`,
  `game`.
- Status: `ssap://audio/getVolume` and
  `ssap://com.webos.applicationManager/getForegroundAppInfo`

## Power on

The SSAP socket is down while the panel is off, so power-on uses Wake-on-LAN
(magic packet to the configured `mac`), the same as the MadVR Envy and the
Trinnov. Enable "Mobile TV On" / Wake-on-LAN in the TV settings.

## Notes

- Picture-mode tokens and the `setSystemSettings` category can vary by webOS
  version; confirm against the live G5 and adjust `PICTURE_MODES` if a preset
  does not apply.
- The WebSocket is injected in the adapter (`transport_factory`), so the message
  protocol is unit-tested without a TV.
