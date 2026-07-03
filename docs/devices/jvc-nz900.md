# Device Integration: JVC DLA-NZ900 Projector

## Status

Protocol known and proven. A working, MIT-licensed Python reference exists: [`iloveicedgreentea/jvc_projector_python`](https://github.com/iloveicedgreentea/jvc_projector_python). The adapter may use this library directly or reimplement against the documented protocol.

## Transport

- Protocol: TCP/IP, raw socket.
- Port: 20554.
- One control connection at a time. Close the connection before other control systems (Roomie) attempt to connect, and vice versa.

## Authentication (required for NZ series)

The NZ800/NZ900 require a network password before IP control works.

1. On the projector, under Network settings, enable the network password option and set a password.
2. The control key is the SHA256 hash of `<password>` concatenated with the literal string `JVCKWPJ`. For example, if the password is `1234567890`, hash the string `1234567890JVCKWPJ` and use the resulting SHA256 hex digest.
3. Ensure the Control4 setting under Network options is turned OFF. While Control4 mode is on, the projector does not expose port 20554.

The `jvc_projector_python` library handles this when constructed as `JVCProjector(host="<ip>", connect_timeout=10, password="<plaintext password>")`; it performs the hashing internally.

## Connection Handshake

For direct-socket implementations, the classic JVC handshake is:

1. Open a TCP connection to port 20554.
2. The projector sends `PJ_OK`.
3. Within five seconds, send `PJREQ` (for NZ models, `PJREQ_<sha256 hex key>`).
4. The projector replies `PJACK`.
5. Send the command within five seconds. The projector closes the connection if idle beyond the window.

## Commands (verified against the reference library)

Commands use the form `command, parameter`.

| Capability | Command | Parameters |
|---|---|---|
| Power on/off | `power` | `on`, `off` |
| Power state (read) | `power` | returns one of `standby`, `on`, `cooling`, `reserved`, `emergency` |
| Input selection | `input_mode` | `hdmi1`, `hdmi2` |
| Source status (read) | `source_status` | returns `logo`, `no_signal`, or `signal` |
| Low latency mode | `low_latency` | `on`, `off` |
| Picture mode | `picture_mode` | `frame_adapt_hdr`, `frame_adapt_hdr2`, `frame_adapt_hdr3`, `hdr_plus`, `hdr`, `hlg`, `pana_pq`, `filmmaker`, `film`, `cinema`, `natural`, `thx`, `user1`–`user6` |

Additional supported commands in the reference library include laser power/dimming, aperture, anamorphic, masking, e-shift, motion enhance, aspect ratio, and menu navigation (`menu`, arrows, `back`). Expose these in the adapter's `capabilities()` as needed.

## Adapter Requirements

1. Implement power on/off, read power state, set and read input, set and read low latency, and set picture mode.
2. `get_status()` returns power state, source status, current input, and low-latency state.
3. Power-on is asynchronous: after sending `power, on`, poll `power` until it returns `on` (the unit passes through `reserved`/`cooling`-style transitions). The Theater On routine depends on this poll (see `docs/usecases/theater-on.md`).
4. Respect the single-connection limit: connect, execute, disconnect, and back off on connection-refused errors that indicate another controller holds the socket.

## Configuration

```yaml
jvc:
  host: "192.168.x.x"
  port: 20554
  # password is provided via the JVC_PASSWORD environment variable, not here
  target_input: "hdmi1"
  target_picture_mode: "frame_adapt_hdr"
```

## References

- Reference library: https://github.com/iloveicedgreentea/jvc_projector_python
- NZ password/auth procedure: https://support.habitech.co.uk/hc/en-us/articles/21543558466205-JVC-NZ800-900-series-control-issues
- JVC D-ILA LAN specification (handshake, port 20554): https://manual3.jvckenwood.com/projector/mobile/dla/b5a-4685-en/BONDSYzjrtjvkr.php
