# Use Case: Theater Off

## Intent

One tap returns the theater to standby cleanly. The projector is the critical device to power down; other devices return to standby or a safe idle state.

## Sequence

1. Emit `started`.
2. JVC: connect (handshake and auth), send `power, off`. Poll `power` until it reports `standby` or a cooling state, with a timeout. Report cooling as an acceptable terminal state (the projector completes its own fan-down).
3. MadVR Envy: send power off over IP control.
4. Trinnov: optionally power off or mute per configuration. Default behavior is configurable (some users keep the processor on). Read back state.
5. Lighting: optionally recall a "lights up" or "off" Hue scene per configuration.
6. Validate: confirm the JVC reports `standby` or `cooling`. Emit per-device results.
7. Emit `completed` with success, partial, or failed.

## Validation Rules

- Success requires the JVC to acknowledge power-off (state `standby` or `cooling`). Other devices are best-effort.
- Do not force-close the JVC connection mid-cooldown in a way that aborts shutdown; send the off command and allow the projector to complete its cycle.

## Idempotency

- If the JVC already reports `standby`, treat the routine as already satisfied and only apply the optional lighting and processor steps.

## Configuration

```yaml
theater_off:
  power_off_trinnov: false      # keep processor on by default
  lighting_scene: "bright"      # scene to recall on shutdown, or null
```

## Progress Events

Same event shape as Theater On: a live checklist under the Theater Off button.
