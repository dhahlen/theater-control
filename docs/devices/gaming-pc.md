# Gaming PC (ASUS ROG) — telemetry

The gaming PC is a source in both rooms (Trinnov Altitude, and routable to the
Pool House). This integration is read-only telemetry: it surfaces the machine's
CPU and GPU temperature, load, and power, plus memory load and every other
sensor, on a Gaming PC tab. There are no control commands.

## Sensor source: Libre Hardware Monitor

Sensors are read from Libre Hardware Monitor, a free, open source hardware
monitor that reads the ASUS motherboard controller, the CPU, and the GPU. It
exposes its full sensor tree as JSON over a built-in web server.

On the PC:

1. Install Libre Hardware Monitor and run it (it must stay running to serve
   data; add it to startup so it launches with Windows).
2. Options -> "Run web server" (default port 8085). Optionally "Minimize to
   tray" and "Start minimized" so it runs unattended.
3. Confirm `http://<pc-ip>:8085/data.json` returns JSON from another machine on
   the subnet.

The web server is unauthenticated on the local network, so no secret is stored.

## Configuration

```yaml
gaming_pc:
  host: "192.168.1.60"   # the PC's IP (static/reserved recommended)
  port: 8085             # Libre Hardware Monitor web server port
  path: "/data.json"     # JSON sensor tree endpoint
```

When the PC is off or the monitor is not running the endpoint is unreachable and
the device reads offline. That offline/online state is also the "gaming PC in
use" signal, so the Gaming PC tab only shows data when the PC is up.

## Parsing

Libre Hardware Monitor returns a nested tree: a machine node, then one node per
hardware (CPU, GPU, motherboard, memory, storage), each with category groups
(Temperatures, Load, Powers, Clocks, Fans, Data) of leaf sensors. The adapter
walks the tree, attributes each leaf to its enclosing hardware (nested super-IO
chips roll up to the motherboard), and picks the headline figures:

- CPU temperature: the package sensor (`Core (Tctl/Tdie)` on AMD, `CPU Package`
  on Intel), falling back to the hottest core.
- CPU load: `CPU Total`. CPU power: the `Package` power.
- GPU temperature, load, and power: the `GPU Core` sensors.
- Memory load: the `Memory` load percentage.

Sensor names vary by CPU/GPU vendor and monitor version, so the selection is by
name substring with fallbacks; the tab also lists every sensor grouped by
hardware. The HTTP client is injected in the adapter, so parsing is unit-tested
against a captured tree without the PC.
