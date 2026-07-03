# Use Case: Theater On

## Intent

One tap brings the theater to a ready-to-watch state for a chosen source. The routine powers the projector, prepares the video processor, waits for the projector to come up, and validates that input, latency mode, and picture profile are correct. It is idempotent: running it when the theater is already on verifies and corrects rather than blindly re-sending.

## Inputs

- `source`: the source to prepare (for example, `kaleidescape`, `plex`, `gaming_pc`). Defaults to a configured default source.
- Target values pulled from `config/devices.yaml`: JVC target input and picture mode, MadVR profile for the source, Trinnov source mapping.

## Preconditions

- JVC network password is set and Control4 mode is off (see `docs/devices/jvc-nz900.md`).
- MadVR Envy MAC address is configured for Wake-on-LAN.
- Backend container is on the theater subnet.

## Sequence

1. Emit `started` progress event.
2. MadVR Envy: send Wake-on-LAN magic packet, then wait until the Envy answers on port 44077 (poll with timeout). This runs in parallel with the JVC power step.
3. JVC: connect (handshake and auth), send `power, on`. Do not assume immediate readiness.
4. JVC: poll `power` until it returns `on`, with a timeout (projector warm-up can take up to roughly 30 to 45 seconds). Emit a progress event on each poll so the UI shows a live "waiting for projector" state. On timeout, return a failure for this step and stop.
5. JVC: set `input_mode` to the target input (for example `hdmi1`). Read it back to confirm.
6. JVC: set `low_latency` to the source-appropriate value (on for `gaming_pc`, off for movie sources) per config. Read it back to confirm.
7. JVC: set `picture_mode` to the target (for example `frame_adapt_hdr` for movies). Confirmation of picture mode is best-effort.
8. MadVR Envy: activate the profile mapped to the source.
9. Trinnov: power on if needed, select the mapped source, and set a safe default or last-known volume. Read back source and volume.
10. Validate: confirm JVC power is `on`, JVC input equals target, JVC low-latency equals target, Trinnov source equals target. Emit per-check results.
11. Emit `completed` with an overall result of success, partial (with the list of failed checks), or failed.

## Validation Rules

- The routine succeeds only if the JVC reports power `on`, the JVC input matches the target, and the JVC low-latency state matches the target. These are the three checks the user explicitly cares about.
- MadVR profile activation and Trinnov source selection are validated where the device reports state; if a device does not confirm, mark the step as "sent, unconfirmed" rather than failed.
- Any step timeout produces a partial result with a clear message identifying the device and step, and a retry affordance in the UI.

## Idempotency

- If the JVC already reports `on`, skip the power and warm-up wait and proceed directly to input/latency/picture validation and correction.
- If the Trinnov already has the correct source, do not re-select it; only correct on mismatch.

## Failure Handling

- JVC single-connection limit: if the connection is refused (another controller holds it), back off and retry a small number of times before failing the step with a clear message.
- If MadVR does not wake within its timeout, continue with the JVC steps and report MadVR as failed, since the projector is the critical path.

## Progress Events (WebSocket)

Each step emits `{ step, status, detail }` where status is one of `pending`, `running`, `ok`, `sent_unconfirmed`, `failed`. The front end renders these as a live checklist under the Theater On button.
