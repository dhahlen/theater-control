from __future__ import annotations

import pytest

from backend.app.adapters.gaming_pc import GamingPcAdapter

# Abridged Libre Hardware Monitor /data.json tree: a computer root with a CPU,
# GPU, motherboard (nested super-IO chip), and memory hardware node.
SAMPLE = {
    "Text": "Sensor",
    "Children": [
        {
            "Text": "DESKTOP-ROG",
            "ImageURL": "images_icon/computer.png",
            "Children": [
                {
                    "Text": "AMD Ryzen 9 9950X",
                    "ImageURL": "images_icon/cpu.png",
                    "Children": [
                        {
                            "Text": "Temperatures",
                            "Children": [
                                {"Text": "Core (Tctl/Tdie)", "Value": "58.4 °C"},
                                {"Text": "CPU Core #1", "Value": "55.0 °C"},
                                {"Text": "CPU Core #2", "Value": "61.2 °C"},
                            ],
                        },
                        {"Text": "Load", "Children": [{"Text": "CPU Total", "Value": "13.5 %"}]},
                        {"Text": "Powers", "Children": [{"Text": "Package", "Value": "72.0 W"}]},
                    ],
                },
                {
                    "Text": "NVIDIA GeForce RTX 4090",
                    "ImageURL": "images_icon/nvidia.png",
                    "Children": [
                        {"Text": "Temperatures", "Children": [{"Text": "GPU Core", "Value": "41.0 °C"}]},
                        {
                            "Text": "Load",
                            "Children": [
                                {"Text": "GPU Core", "Value": "4.0 %"},
                                {"Text": "GPU Memory", "Value": "18.0 %"},
                            ],
                        },
                        {"Text": "Powers", "Children": [{"Text": "GPU Package", "Value": "95.5 W"}]},
                        {"Text": "Data", "Children": [{"Text": "GPU Memory Used", "Value": "3.2 GB"}]},
                    ],
                },
                {
                    "Text": "ASUS ROG STRIX X870E-E GAMING WIFI",
                    "ImageURL": "images_icon/mainboard.png",
                    "Children": [
                        {
                            "Text": "Nuvoton NCT6798D",
                            "Children": [
                                {"Text": "Temperatures", "Children": [{"Text": "CPU", "Value": "45.0 °C"}]},
                                {"Text": "Fans", "Children": [{"Text": "CPU Fan", "Value": "820 RPM"}]},
                            ],
                        }
                    ],
                },
                {
                    "Text": "Generic Memory",
                    "ImageURL": "images_icon/ram.png",
                    "Children": [
                        {"Text": "Load", "Children": [{"Text": "Memory", "Value": "34.7 %"}]},
                    ],
                },
            ],
        }
    ],
}


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class FakeClient:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.requested: list[str] = []

    async def get(self, path: str) -> FakeResponse:
        self.requested.append(path)
        return FakeResponse(self._payload)

    async def aclose(self) -> None:
        return None


class FailingClient:
    async def get(self, path: str):  # noqa: ANN201
        raise ConnectionError("connection refused")

    async def aclose(self) -> None:
        return None


def _adapter(payload: object = SAMPLE) -> GamingPcAdapter:
    return GamingPcAdapter("gaming_pc", "10.0.0.5", client=FakeClient(payload))


async def test_headline_cpu_gpu_figures():
    adapter = _adapter()
    status = await adapter.get_status()
    e = status.extra
    assert status.reachable.value == "online"
    assert e["cpu_name"] == "AMD Ryzen 9 9950X"
    assert e["gpu_name"] == "NVIDIA GeForce RTX 4090"
    # Prefers the Tctl/Tdie package sensor over the per-core temps.
    assert e["cpu_temp"] == 58.4
    assert e["cpu_load"] == 13.5
    assert e["cpu_power"] == 72.0
    assert e["gpu_temp"] == 41.0
    assert e["gpu_load"] == 4.0  # GPU Core load, not GPU Memory load
    assert e["gpu_power"] == 95.5
    assert e["memory_load"] == 34.7


async def test_groups_preserve_hardware_and_units():
    adapter = _adapter()
    status = await adapter.get_status()
    groups = {g["hardware"]: g for g in status.extra["groups"]}
    assert set(groups) == {
        "AMD Ryzen 9 9950X",
        "NVIDIA GeForce RTX 4090",
        "ASUS ROG STRIX X870E-E GAMING WIFI",
        "Generic Memory",
    }
    assert groups["AMD Ryzen 9 9950X"]["kind"] == "cpu"
    assert groups["NVIDIA GeForce RTX 4090"]["kind"] == "gpu"
    assert groups["ASUS ROG STRIX X870E-E GAMING WIFI"]["kind"] == "motherboard"
    # The nested super-IO chip's fan is attributed to the motherboard.
    fan = [s for s in groups["ASUS ROG STRIX X870E-E GAMING WIFI"]["sensors"] if s["name"] == "CPU Fan"]
    assert fan and fan[0]["value"] == 820.0 and fan[0]["unit"] == "RPM"


async def test_cpu_temp_falls_back_to_hottest_core():
    # A CPU that only exposes per-core temps: the hottest core is used.
    payload = {
        "Text": "Sensor",
        "Children": [
            {
                "Text": "Intel Core i9",
                "ImageURL": "images_icon/cpu.png",
                "Children": [
                    {
                        "Text": "Temperatures",
                        "Children": [
                            {"Text": "CPU Core #1", "Value": "50.0 °C"},
                            {"Text": "CPU Core #2", "Value": "67.0 °C"},
                        ],
                    }
                ],
            }
        ],
    }
    status = await _adapter(payload).get_status()
    assert status.extra["cpu_temp"] == 67.0


async def test_offline_when_endpoint_unreachable():
    adapter = GamingPcAdapter("gaming_pc", "10.0.0.5", client=FailingClient())
    status = await adapter.get_status()
    assert status.reachable.value == "offline"


async def test_send_has_no_commands():
    adapter = _adapter()
    with pytest.raises(ValueError):
        await adapter.send("anything")
    assert adapter.capabilities() == []


async def test_polls_configured_path():
    client = FakeClient(SAMPLE)
    adapter = GamingPcAdapter("gaming_pc", "10.0.0.5", path="custom.json", client=client)
    await adapter.get_status()
    assert client.requested == ["/custom.json"]
