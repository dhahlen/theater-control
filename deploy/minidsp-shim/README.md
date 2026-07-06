# MiniDSP CLI shim

A small host service that gives theater-control a reliable control path to the
miniDSP SHD.

## Why

The SHD is controlled over USB. The upstream minidsp-rs daemon (`minidspd`)
holds the device open persistently, and on some hosts that wedges the SHD's USB
HID after a short time (the HTTP API hangs, the device reads time out) even
though the hardware is healthy. The one-shot `minidsp` CLI, which opens, reads,
and closes the device per invocation, is reliable on the same host.

This shim serves the subset of the minidsp-rs HTTP API that the theater-control
`minidsp` adapter uses, backed by the CLI instead of the persistent daemon. It
binds the same address the daemon used (`127.0.0.1:5380`), so no application
change is needed.

## Requirements

- The `minidsp` CLI at `/usr/local/bin/minidsp` (from the minidsp-rs release).
- `minidspd` stopped and disabled, so the CLI talks straight to USB.
- Runs natively as root (USB HID access), not in a container.

## Install

```bash
# Stop and disable the unreliable daemon and its watchdog
sudo systemctl disable --now minidspd
sudo systemctl disable --now minidspd-watchdog.timer 2>/dev/null || true
sudo rm -f /etc/systemd/system/minidspd-watchdog.service \
           /etc/systemd/system/minidspd-watchdog.timer \
           /usr/local/bin/minidspd-watchdog.sh

# Install the shim and its unit
sudo install -m 755 minidsp-shim.py /usr/local/bin/minidsp-shim.py
sudo install -m 644 minidsp-shim.service /etc/systemd/system/minidsp-shim.service

sudo systemctl daemon-reload
sudo systemctl enable --now minidsp-shim.service

# Verify
curl -s http://127.0.0.1:5380/devices/0
```

## Endpoints

- `GET /devices` — presence list.
- `GET /devices/0` — `{ master: { preset, source, volume, mute }, output_levels: [...] }`.
- `POST /devices/0/config` — `{ master_status: { volume, mute }, outputs: [ { index, gain, mute } ] }`.

The theater-control `minidsp` config block is unchanged (`host: 127.0.0.1`,
`port: 5380`).
