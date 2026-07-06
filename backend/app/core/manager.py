"""Device manager: builds adapters from config and owns the poll loop.

This is the seam between configuration, the adapter layer, and the live state
model. It constructs one adapter per configured device, polls them on an
interval, writes results into the StateStore, and publishes deltas on the
EventBus. Orchestration and the API reach adapters through this manager so
there is a single place that owns connection lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..adapters.base import DeviceAdapter, DeviceStatus, Reachability
from .config import AppConfig
from .events import EventBus, device_event
from .state import StateStore

log = logging.getLogger("theater.manager")


class DeviceManager:
    def __init__(self, config: AppConfig, state: StateStore, bus: EventBus) -> None:
        self._config = config
        self._state = state
        self._bus = bus
        self._adapters: dict[str, DeviceAdapter] = {}
        self._poll_task: asyncio.Task[None] | None = None
        self._build_adapters()

    # -- construction -----------------------------------------------------

    def _build_adapters(self) -> None:
        # Imported here to keep the adapter layer free of core->adapter cycles
        # at import time and to tolerate optional third-party device libraries.
        from ..adapters.jvc import JvcAdapter
        from ..adapters.trinnov import TrinnovAdapter
        from ..adapters.madvr import MadvrAdapter
        from ..adapters.hue import HueAdapter
        from ..adapters.kaleidescape import KaleidescapeAdapter
        from ..adapters.plex import PlexAdapter

        cfg = self._config

        if cfg.jvc:
            self._adapters["jvc"] = JvcAdapter(
                device_id="jvc",
                host=cfg.jvc.host,
                port=cfg.jvc.port,
                password=cfg.secrets.jvc_password or "",
            )
        if cfg.trinnov:
            self._adapters["trinnov"] = TrinnovAdapter(
                device_id="trinnov",
                host=cfg.trinnov.host,
                port=cfg.trinnov.port,
                sources=cfg.trinnov.sources,
                mac=cfg.trinnov.mac,
            )
        if cfg.madvr:
            self._adapters["madvr"] = MadvrAdapter(
                device_id="madvr",
                host=cfg.madvr.host,
                mac=cfg.madvr.mac,
                port=cfg.madvr.port,
                heartbeat_seconds=cfg.madvr.heartbeat_seconds,
                profile_macros=cfg.madvr.profile_macros,
            )
        if cfg.hue:
            self._adapters["hue"] = HueAdapter(
                device_id="hue",
                bridge_ip=cfg.hue.bridge_ip,
                app_key=cfg.secrets.hue_app_key or "",
                room_group_id=cfg.hue.room_group_id,
                scenes=cfg.hue.scenes,
            )
        if cfg.kaleidescape:
            self._adapters["kaleidescape"] = KaleidescapeAdapter(
                device_id="kaleidescape",
                host=cfg.kaleidescape.host,
                port=cfg.kaleidescape.port,
                cpdid=cfg.kaleidescape.device_id,
            )
        if cfg.plex:
            self._adapters["plex"] = PlexAdapter(
                device_id="plex",
                base_url=cfg.plex.base_url,
                token=cfg.secrets.plex_token or "",
                default_player_id=cfg.plex.default_player_id,
                web_url=cfg.plex.web_url,
                tautulli_url=cfg.tautulli.base_url if cfg.tautulli else "",
                tautulli_key=cfg.secrets.tautulli_api_key or "",
            )
        if cfg.gaming_pc:
            from ..adapters.gaming_pc import GamingPcAdapter

            self._adapters["gaming_pc"] = GamingPcAdapter(
                device_id="gaming_pc",
                host=cfg.gaming_pc.host,
                port=cfg.gaming_pc.port,
                path=cfg.gaming_pc.path,
            )
        if cfg.minidsp:
            from ..adapters.minidsp import MiniDspAdapter

            self._adapters["minidsp"] = MiniDspAdapter(
                device_id="minidsp",
                host=cfg.minidsp.host,
                port=cfg.minidsp.port,
                device_index=cfg.minidsp.device_index,
                outputs=cfg.minidsp.outputs,
                master_min_db=cfg.minidsp.master_min_db,
                output_min_db=cfg.minidsp.output_min_db,
                output_max_db=cfg.minidsp.output_max_db,
            )

        self._build_poolhouse_adapters()

    def _build_poolhouse_adapters(self) -> None:
        """Register the Pool House room's devices under ph_* ids (Phase 2).

        The Altitude 16, Office Hue zones, and Pool House Plex target reuse the
        existing adapters; the LG G5 uses its own webOS adapter.
        """

        cfg = self._config
        ph = cfg.poolhouse
        if not ph:
            return

        from ..adapters.trinnov import TrinnovAdapter
        from ..adapters.hue import HueAdapter
        from ..adapters.plex import PlexAdapter

        if ph.trinnov:
            self._adapters["ph_trinnov"] = TrinnovAdapter(
                device_id="ph_trinnov",
                host=ph.trinnov.host,
                port=ph.trinnov.port,
                sources=ph.trinnov.sources,
                mac=ph.trinnov.mac,
            )
        if ph.hue:
            for zone_key, zone in ph.hue.zones.items():
                self._adapters[f"ph_hue_{zone_key}"] = HueAdapter(
                    device_id=f"ph_hue_{zone_key}",
                    bridge_ip=ph.hue.bridge_ip,
                    app_key=cfg.secrets.hue_poolhouse_app_key or "",
                    room_group_id=zone.group,
                    scenes=zone.scenes,
                )
        if ph.plex and cfg.plex:
            self._adapters["ph_plex"] = PlexAdapter(
                device_id="ph_plex",
                base_url=cfg.plex.base_url,
                token=cfg.secrets.plex_token or "",
                default_player_id=ph.plex.player_id,
                web_url=cfg.plex.web_url,
                tautulli_url=cfg.tautulli.base_url if cfg.tautulli else "",
                tautulli_key=cfg.secrets.tautulli_api_key or "",
            )
        if ph.lg:
            from ..adapters.lg import LgAdapter

            self._adapters["ph_lg"] = LgAdapter(
                device_id="ph_lg",
                host=ph.lg.host,
                port=ph.lg.port,
                client_key=cfg.secrets.lg_client_key or "",
                mac=ph.lg.mac,
                inputs=ph.lg.inputs,
            )
        if ph.shield:
            from ..adapters.shield import ShieldAdapter

            self._adapters["ph_shield"] = ShieldAdapter(
                device_id="ph_shield",
                host=ph.shield.host,
                port=ph.shield.port,
                key_dir=ph.shield.key_dir,
            )

    # -- accessors --------------------------------------------------------

    @property
    def adapters(self) -> dict[str, DeviceAdapter]:
        return self._adapters

    def get(self, device_id: str) -> DeviceAdapter | None:
        return self._adapters.get(device_id)

    # -- lifecycle --------------------------------------------------------

    async def start(self) -> None:
        """Connect adapters (best-effort) and start the poll loop."""

        await asyncio.gather(
            *(self._safe_connect(a) for a in self._adapters.values()),
            return_exceptions=True,
        )
        self._poll_task = asyncio.create_task(self._poll_loop(), name="poller")

    async def stop(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        await asyncio.gather(
            *(self._safe_disconnect(a) for a in self._adapters.values()),
            return_exceptions=True,
        )

    async def _safe_connect(self, adapter: DeviceAdapter) -> None:
        try:
            await adapter.connect()
        except Exception as exc:  # degrade gracefully; do not refuse to start
            log.warning("connect failed for %s: %s", adapter.device_id, exc)

    async def _safe_disconnect(self, adapter: DeviceAdapter) -> None:
        try:
            await adapter.disconnect()
        except Exception as exc:
            log.debug("disconnect error for %s: %s", adapter.device_id, exc)

    # -- polling ----------------------------------------------------------

    async def _poll_loop(self) -> None:
        interval = self._config.poll_interval_s
        while True:
            await self.poll_once()
            await asyncio.sleep(interval)

    async def poll_once(self) -> None:
        results = await asyncio.gather(
            *(self._poll_adapter(a) for a in self._adapters.values()),
            return_exceptions=True,
        )
        for adapter, result in zip(self._adapters.values(), results):
            if isinstance(result, Exception):
                log.debug("poll error for %s: %s", adapter.device_id, result)

    async def _poll_adapter(self, adapter: DeviceAdapter) -> None:
        try:
            status = await asyncio.wait_for(adapter.get_status(), timeout=5.0)
        except Exception:
            status = DeviceStatus(
                device_id=adapter.device_id, reachable=Reachability.OFFLINE
            )
        await self._publish_status(status)

    async def _publish_status(self, status: DeviceStatus) -> None:
        state = await self._state.update_from_status(status)
        from dataclasses import asdict

        await self._bus.publish(device_event(status.device_id, asdict(state)))

    # -- command dispatch -------------------------------------------------

    async def send_command(
        self, device_id: str, command: str, params: dict[str, Any] | None = None
    ) -> Any:
        adapter = self._adapters.get(device_id)
        if adapter is None:
            raise KeyError(device_id)
        result = await adapter.send(command, params or {})
        # Refresh state right after a command so the UI reflects the change fast.
        try:
            status = await asyncio.wait_for(adapter.get_status(), timeout=5.0)
            await self._publish_status(status)
        except Exception:
            pass
        return result
