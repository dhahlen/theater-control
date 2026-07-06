"""Gaming PC sensor adapter (Libre Hardware Monitor).

Read-only telemetry for the ASUS ROG gaming PC. Libre Hardware Monitor runs on
the PC with its "Remote Web Server" enabled, which serves the full sensor tree
as JSON at ``http://<pc>:8085/data.json``. This adapter polls that endpoint and
normalizes it into headline figures (CPU and GPU temperature, load, and power,
plus memory load) and a grouped sensor list for the Gaming PC tab.

There are no commands: the PC is monitored, not controlled. When the PC is off
or the monitor is not running the endpoint is unreachable and the device reads
offline, which is also the "gaming PC in use" signal for the UI.

The HTTP client is injected for unit tests. See docs/devices/gaming-pc.md.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import Capability, DeviceAdapter, DeviceStatus, Reachability

log = logging.getLogger("theater.gaming_pc")

# Libre Hardware Monitor groups a hardware node's leaf sensors under category
# nodes with these names.
CATEGORIES = frozenset(
    {"Voltages", "Temperatures", "Load", "Clocks", "Powers", "Fans", "Data", "Levels"}
)

# Icon fragments that mark a node as top-level hardware (stable across brands).
HARDWARE_ICONS = ("cpu", "nvidia", "ati", "amd", "mainboard", "ram", "hdd", "ssd", "nvme")


def _hardware_kind(text: str, image_url: str) -> str:
    """Classify a top-level hardware node as cpu/gpu/motherboard/memory/etc.

    Uses the node's icon first (stable across CPU/GPU brands), then falls back to
    keywords in its name so a renamed or unknown icon still classifies.
    """

    t = text.lower()
    img = (image_url or "").lower()
    if "cpu" in img or any(k in t for k in ("ryzen", "core i", "threadripper", "xeon", "cpu")):
        return "cpu"
    if any(k in img for k in ("nvidia", "ati", "amd")) or any(
        k in t for k in ("geforce", "radeon", "nvidia", "rtx", "gtx", "intel arc")
    ):
        return "gpu"
    if "mainboard" in img or any(k in t for k in ("strix", "gaming wifi", "mainboard", "motherboard")):
        return "motherboard"
    if "ram" in img or "memory" in t:
        return "memory"
    if any(k in img for k in ("hdd", "ssd")) or any(k in t for k in ("nvme", "ssd", "hdd")):
        return "storage"
    if "network" in img:
        return "network"
    return "other"


def _parse_value(raw: Any) -> tuple[float | None, str]:
    """Split a Libre Hardware Monitor value like "55.2 °C" into (55.2, "°C")."""

    if not isinstance(raw, str):
        return None, ""
    text = raw.strip()
    if not text or text in ("-", "N/A"):
        return None, ""
    parts = text.split(" ", 1)
    number = parts[0].replace(",", "")
    unit = parts[1].strip() if len(parts) > 1 else ""
    try:
        return float(number), unit
    except ValueError:
        return None, ""


def _is_hardware(text: str, image_url: str) -> bool:
    """True for a top-level hardware node (CPU, GPU, motherboard, memory, ...).

    Recognized by a hardware icon or a hardware-shaped name. The machine/computer
    root and nested super-IO chips are not hardware, so their sensors stay
    attributed to the enclosing hardware.
    """

    img = (image_url or "").lower()
    if "computer" in img:  # the machine root, not a piece of hardware
        return False
    if any(icon in img for icon in HARDWARE_ICONS):
        return True
    return _hardware_kind(text, image_url) != "other"


def _flatten(root: dict[str, Any]) -> list[dict[str, Any]]:
    """Walk the sensor tree into a flat list of leaf sensors.

    Each sensor carries its hardware name, hardware kind, category, sensor name,
    numeric value, and unit. The first recognized hardware node on a path sets
    the hardware context (so the tree may be wrapped in a machine node or not),
    and nodes named after a category set the category for their descendants.
    """

    sensors: list[dict[str, Any]] = []

    def walk(node: dict[str, Any], hardware: str, kind: str, category: str) -> None:
        text = str(node.get("Text", ""))
        children = node.get("Children") or []
        if text in CATEGORIES:
            category = text
        elif not hardware and _is_hardware(text, str(node.get("ImageURL", ""))):
            hardware = text
            kind = _hardware_kind(text, str(node.get("ImageURL", "")))
        value, unit = _parse_value(node.get("Value"))
        if value is not None and not children and hardware:
            sensors.append(
                {
                    "hardware": hardware,
                    "kind": kind,
                    "category": category,
                    "name": text,
                    "value": value,
                    "unit": unit,
                }
            )
        for child in children:
            walk(child, hardware, kind, category)

    walk(root, "", "other", "")
    return sensors


def _pick(
    sensors: list[dict[str, Any]],
    kind: str,
    category: str,
    prefer: tuple[str, ...] = (),
    aggregate: str | None = None,
) -> float | None:
    """Choose one value from a (kind, category) group.

    Tries each ``prefer`` name substring in order; failing that, either returns
    the max of the group (``aggregate="max"``) or the first sensor found.
    """

    group = [s for s in sensors if s["kind"] == kind and s["category"] == category]
    if not group:
        return None
    for want in prefer:
        for s in group:
            if want.lower() in s["name"].lower():
                return s["value"]
    if aggregate == "max":
        return max(s["value"] for s in group)
    return group[0]["value"]


def _headline(sensors: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract the figures the dashboard and status readout show."""

    cpu_name = next((s["hardware"] for s in sensors if s["kind"] == "cpu"), None)
    gpu_name = next((s["hardware"] for s in sensors if s["kind"] == "gpu"), None)
    return {
        "cpu_name": cpu_name,
        "gpu_name": gpu_name,
        # AMD reports "Core (Tctl/Tdie)"; Intel "CPU Package"; else hottest core.
        "cpu_temp": _pick(
            sensors, "cpu", "Temperatures",
            prefer=("Tctl", "Package", "Core (Tctl"), aggregate="max",
        ),
        "cpu_load": _pick(sensors, "cpu", "Load", prefer=("CPU Total", "Total")),
        "cpu_power": _pick(sensors, "cpu", "Powers", prefer=("Package", "CPU Package")),
        "gpu_temp": _pick(sensors, "gpu", "Temperatures", prefer=("GPU Core", "Core", "Hot Spot")),
        "gpu_load": _pick(sensors, "gpu", "Load", prefer=("GPU Core", "Core")),
        "gpu_power": _pick(sensors, "gpu", "Powers", prefer=("GPU Package", "Package", "GPU Power")),
        "memory_load": _pick(sensors, "memory", "Load", prefer=("Memory",)),
    }


def _groups(sensors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group sensors by hardware for the tab, preserving discovery order."""

    order: list[str] = []
    by_hardware: dict[str, dict[str, Any]] = {}
    for s in sensors:
        hw = s["hardware"]
        if hw not in by_hardware:
            order.append(hw)
            by_hardware[hw] = {"hardware": hw, "kind": s["kind"], "sensors": []}
        by_hardware[hw]["sensors"].append(
            {"category": s["category"], "name": s["name"], "value": s["value"], "unit": s["unit"]}
        )
    return [by_hardware[hw] for hw in order]


class GamingPcAdapter(DeviceAdapter):
    def __init__(
        self,
        device_id: str,
        host: str,
        port: int = 8085,
        path: str = "/data.json",
        client: Any | None = None,
    ) -> None:
        self.device_id = device_id
        self._host = host
        self._port = port
        self._path = path if path.startswith("/") else f"/{path}"
        self._client = client

    def _http(self) -> Any:
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=f"http://{self._host}:{self._port}", timeout=4.0
            )
        return self._client

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> None:
        # HTTP is connectionless; nothing to establish.
        return None

    async def disconnect(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass

    # -- status -----------------------------------------------------------

    async def get_status(self) -> DeviceStatus:
        try:
            resp = await self._http().get(self._path)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            log.debug("gaming_pc get_status failed: %s", exc)
            return DeviceStatus(device_id=self.device_id, reachable=Reachability.OFFLINE)

        sensors = _flatten(data if isinstance(data, dict) else {})
        extra = _headline(sensors)
        extra["groups"] = _groups(sensors)
        return DeviceStatus(
            device_id=self.device_id,
            reachable=Reachability.ONLINE,
            power="on",
            extra=extra,
        )

    # -- commands ---------------------------------------------------------

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        # Telemetry only: the PC is monitored, not controlled from here.
        raise ValueError(f"gaming_pc has no commands (got {command!r})")

    # -- capabilities -----------------------------------------------------

    def capabilities(self) -> list[Capability]:
        return []
