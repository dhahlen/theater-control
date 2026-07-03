# Device Integration: AVPro Edge AC-MX-44X (Phase 2)

## Status

Phase 2. Protocol documented; adapter is stubbed in phase 1 so the routing logic slots in without rework. This 4x4 HDMI matrix is used to switch the gaming PC between the theater and the pool house display.

## Transport

- Protocol: TCP/IP over the LAN, or RS-232.
- IP control port: 23 (Telnet). Ensure the device's web configuration has the control port set to 23. RS-232 default is 57600 baud, 8N1, no flow control.
- To find the device IP from the front panel, press and hold the Input 3 and Input 4 buttons together for about three seconds.

## Command Set

- Line-oriented ASCII commands. `GET STA` returns current status including the IP address and routing. Routing commands set input-to-output mapping. Confirm the exact routing command syntax against the AC-MX-44X manual (the AC-MX series shares a common command language).
- A raw API pass-through is supported for commands not covered by higher-level drivers.

## Required Capabilities (Phase 2)

| Capability | Purpose |
|---|---|
| Route input to output | Send the gaming PC (an input) to the theater output or the pool house output |
| Read routing state | Report where the gaming PC is currently routed |
| Get status | Health, IP, and current matrix state |

## Adapter Requirements

1. Model the matrix as named inputs and outputs in config (gaming PC input, theater output, pool house output).
2. Provide a single high-level action, "send gaming PC to <room>", that issues the correct route command.
3. Include in status the current destination so the UI can show where the PC is displayed.

## Configuration

```yaml
ac_mx_44x:
  host: "192.168.x.x"
  port: 23
  inputs:
    gaming_pc: 1
  outputs:
    theater: 1
    pool_house: 2
```

## References

- AC-MX series manual (control over TCP/IP and RS-232, GET STA): https://adeogroup.it/sites/default/files/prodotti_allegati_pubblici/avpro_AC-MX-42%20Manual.pdf
- AC-MX-44X product page: https://www.avproglobal.com/products/ac-mx-44x
- RTI driver (TCP port 23, routing, API pass-through): https://driverstore.rticontrol.com/driver/avpro-edge-ac-mxxx-series-models
