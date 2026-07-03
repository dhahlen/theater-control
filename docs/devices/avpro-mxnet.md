# Device Integration: AVPro Edge MXNet (Phase 2)

## Status

Phase 2. Protocol documented; adapter is stubbed in phase 1. MXNet is the AV-over-IP distribution system; all control flows through the MXNet Control Box (CBOX).

## Transport

- Protocol: Telnet / TCP socket to the CBOX.
- Port: 24.
- All routing, RS-232, CEC, and IR pass-through is centralized at the CBOX. Confirm the CBOX generation (1G, 10G, USP, or Dante) because the API document differs slightly per generation.
- Find the CBOX IP on its front-panel LCD (press the Status Monitor button). Default factory IP is 192.168.1.239; web GUI login is admin/admin.

## Command Set

- Line-oriented ASCII over port 24. Confirm which is your CBOX API version. Useful sanity commands: `config get version` and `config get name`.
- Routing binds encoders (inputs) to decoders (outputs). RS-232/CEC/IR commands can be fed to specific decoders for local device control.

## Required Capabilities (Phase 2)

| Capability | Purpose |
|---|---|
| Route encoder to decoder | Distribute a source to a display/zone |
| Recall routing preset | One-tap distribution layouts |
| Send RS-232/CEC to a decoder | Local control of the device at a display (for example, power the LG G5) |
| Get status | CBOX health and current routing |

## Adapter Requirements

1. Model encoders and decoders by friendly name in config, mapped to their MXNet identifiers.
2. Provide high-level routing actions and preset recall.
3. Because MXNet can pass RS-232/CEC to decoders, the pool house display (LG G5) power control can be routed through MXNet if a direct display adapter is not preferred.

## Configuration

```yaml
mxnet:
  cbox_host: "192.168.x.x"
  cbox_port: 24
  encoders:
    gaming_pc: "<encoder-id>"
  decoders:
    theater: "<decoder-id>"
    pool_house: "<decoder-id>"
```

## References

- MXNet API how-to (Telnet, port 24): https://support.avproglobal.com/portal/en/kb/articles/mxnet-api
- ELAN MXNet CBOX driver (TCP port 24, RS-232/CEC): https://support.avproedge.com/portal/en/kb/articles/elan-mxnet-1g-cbox-driver
- MXNet quick start (CBOX IP on front panel, admin/admin): https://support.avproglobal.com/portal/en/kb/articles/mxnet-quick-start-guide
