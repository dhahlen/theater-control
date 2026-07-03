# Use Case: Trinnov Control

## Intent

Direct control of the Trinnov Altitude CI: input/source selection and volume adjustment, replacing the standalone Trinnov interface that currently occupies one of the three iPad split-view panes.

## Behavior

1. Volume: a large, touch-friendly control supporting both a slider (absolute set) and step up/down buttons (relative). Shows the current level, read from the processor.
2. Mute: a mute toggle reflecting current mute state.
3. Source select: buttons for the mapped sources (Kaleidescape, Plex, MadVR, Gaming PC) defined in `config/devices.yaml`, with the active source highlighted.
4. Live state: because the adapter holds a persistent connection and parses asynchronous updates, volume, mute, and source changes made from any controller (the Trinnov remote, its own app, or Theater On) are reflected here in real time.

## Adapter

- Uses the Trinnov adapter (`docs/devices/trinnov-altitude.md`) over TCP port 44100. The exact command tokens for volume and source select must be confirmed against the official Trinnov IP control protocol document before implementation; the transport and connection behavior are confirmed.

## Safety

- Constrain the volume slider to a configured safe maximum to prevent accidental full-scale volume from a touch mistake on the iPad.

## Feedback

- Volume and source actions reflect immediately from the processor's asynchronous state, so the panel always shows true device state rather than optimistic UI state.
