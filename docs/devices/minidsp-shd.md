# MiniDSP SHD — seat transducers (bass shakers)

The SHD drives the seat transducers (bass shakers). The room feeds the front
seat row from XLR Out 1 and the rear row from XLR Out 2, so the integration
gives a master level plus a per-row gain and on/off (mute), letting either row
be turned down or off independently.

## Control path: minidsp-rs daemon over USB

The SHD's DSP is controlled over USB (its built-in Ethernet is for the streamer,
not the DSP). Control goes through `minidspd`, the daemon from the open source
[minidsp-rs](https://github.com/mrene/minidsp-rs) project, which the SHD is
explicitly supported by. The daemon runs on the host with the SHD connected by
USB and exposes an HTTP API; this adapter talks to that daemon, never the SHD
directly. Because theater-control uses host networking, the daemon is reached at
`127.0.0.1:5380`.

### Running the daemon

Install `minidsp-rs` on the Ubuntu host and run `minidspd`. It auto-detects the
SHD on USB. Confirm it is up:

```bash
curl http://127.0.0.1:5380/devices/0
```

That returns the master status (volume, mute, preset, source) and the four
output levels. Enable the HTTP server's TCP bind in the daemon config
(`/etc/minidsp/config.toml`) so the container can reach it on localhost.

## HTTP shapes used

- Status: `GET /devices/0` -> `{master:{volume,mute,preset,source}, output_levels:[...]}`
- Master: `POST /devices/0/config` `{"master_status": {"volume": <db>, "mute": <bool>}}`
- Output: `POST /devices/0/config` `{"outputs": [{"index": <n>, "gain": <db>, "mute": <bool>}]}`

The daemon reports master volume and mute but not the configured per-output gain
and mute, so the row gain and on/off are tracked optimistically from the last
command (the master level is authoritative from the daemon). Output channels are
0-based; map them to friendly row names in config.

## Configuration

```yaml
minidsp:
  host: "127.0.0.1"
  port: 5380
  device_index: 0
  outputs:
    front_row: 0        # XLR Out 1
    rear_row: 1         # XLR Out 2
  master_min_db: -80.0
  output_min_db: -40.0
  output_max_db: 0.0
```

Confirm the output-index mapping against the SHD's routing in the miniDSP Device
Console (which output feeds which XLR jack) and adjust `outputs` if needed. When
`minidspd` is not running or the SHD is unplugged the device reads offline.
