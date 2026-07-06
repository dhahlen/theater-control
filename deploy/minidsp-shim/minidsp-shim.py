#!/usr/bin/env python3
"""Tiny host shim exposing the minidsp CLI over the minidsp-rs HTTP shape.

The minidsp-rs daemon (minidspd) wedges the miniDSP SHD's USB HID when it holds
the device open persistently on some hosts, but the one-shot `minidsp` CLI is
reliable. This shim serves the subset of the minidsp-rs HTTP API that the
theater-control adapter uses by shelling out to the CLI per request, so the
device is opened, read, and closed each time (the pattern that works).

It listens on the same address the daemon used (127.0.0.1:5380), so
theater-control needs no change: point the `minidsp` config block at this host
and port as before. Run it as root (USB HID access) via systemd, with minidspd
stopped and disabled so the CLI talks straight to USB.

Endpoints:
  GET  /devices            -> [ { url, product_name } ]              (presence)
  GET  /devices/0          -> { master:{preset,source,volume,mute}, output_levels:[...] }
  POST /devices/0/config   -> { master_status:{volume,mute}, outputs:[{index,gain,mute}] }

No third-party dependencies: standard library only.
"""

from __future__ import annotations

import json
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MINIDSP = "/usr/local/bin/minidsp"
BIND = ("127.0.0.1", 5380)
CLI_TIMEOUT = 8.0

# Serialize all CLI access: one `minidsp` process touches the USB HID at a time.
_lock = threading.Lock()

_STATUS_RE = re.compile(
    r"preset:\s*(\d+).*?source:\s*(\w+).*?volume:\s*Gain\(([-\d.]+)\).*?mute:\s*(true|false)",
    re.S,
)
_LEVELS_RE = re.compile(r"Output levels:\s*(.*)")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [MINIDSP, *args], capture_output=True, text=True, timeout=CLI_TIMEOUT
    )


def read_status() -> dict:
    result = _run([])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "minidsp CLI failed")
    match = _STATUS_RE.search(result.stdout)
    if not match:
        raise RuntimeError(f"could not parse status: {result.stdout[:200]!r}")
    preset, source, volume, mute = match.groups()
    levels_match = _LEVELS_RE.search(result.stdout)
    levels = (
        [float(x) for x in levels_match.group(1).split(",") if x.strip()]
        if levels_match
        else []
    )
    return {
        "master": {
            "preset": int(preset),
            "source": source,
            "volume": float(volume),
            "mute": mute == "true",
        },
        "output_levels": levels,
    }


def apply_config(body: dict) -> None:
    master = body.get("master_status") or {}
    if "volume" in master:
        _run(["gain", "--", str(float(master["volume"]))])
    if "mute" in master:
        _run(["mute", "on" if master["mute"] else "off"])
    for output in body.get("outputs") or []:
        index = int(output["index"])
        if "gain" in output:
            _run(["output", str(index), "gain", "--", str(float(output["gain"]))])
        if "mute" in output:
            _run(["output", str(index), "mute", "on" if output["mute"] else "off"])


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: object) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.rstrip("/") or "/"
        if path == "/devices":
            return self._send(200, [{"url": "cli", "product_name": "MiniDSP SHD"}])
        if path != "/devices/0":
            return self._send(404, {"error": "not found"})
        try:
            with _lock:
                self._send(200, read_status())
        except Exception as exc:  # daemon-style: report unreachable, do not crash
            self._send(503, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/devices/0/config":
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            with _lock:
                apply_config(body)
                status = read_status()
            self._send(200, status)
        except Exception as exc:
            self._send(503, {"error": str(exc)})

    def log_message(self, *args: object) -> None:  # keep journald quiet
        return


def main() -> None:
    server = ThreadingHTTPServer(BIND, Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
