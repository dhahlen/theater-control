"""Scene registry: maps scene names to orchestration routines.

The API calls ``Orchestrator.run(name, params)``. Each routine coordinates
multiple adapters, emits progress events over the event bus so the front end
can show a live checklist, and returns a structured result.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from ..core.config import AppConfig
from ..core.events import EventBus, progress_event, routine_event
from ..core.manager import DeviceManager
from .theater_off import run_theater_off
from .theater_on import RoutineResult, StepResult, run_theater_on

log = logging.getLogger("theater.orchestration")


class Orchestrator:
    def __init__(self, config: AppConfig, manager: DeviceManager, bus: EventBus) -> None:
        self._config = config
        self._manager = manager
        self._bus = bus

    async def run(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        if name == "theater-on":
            source = params.get("source") or self._config.default_source
            result = await self._run_theater_on(source)
        elif name == "theater-off":
            result = await self._run_theater_off()
        else:
            raise KeyError(name)

        payload = asdict(result)
        await self._bus.publish(routine_event(name, payload))
        return payload

    def _emitter(self, scene: str):
        async def emit(step: StepResult) -> None:
            await self._bus.publish(progress_event(scene, asdict(step)))

        return emit

    async def _run_theater_on(self, source: str) -> RoutineResult:
        return await run_theater_on(
            source=source,
            adapters=self._manager.adapters,
            config=self._config.model_dump(),
            emit=self._emitter("theater-on"),
        )

    async def _run_theater_off(self) -> RoutineResult:
        return await run_theater_off(
            adapters=self._manager.adapters,
            config=self._config.model_dump(),
            emit=self._emitter("theater-off"),
        )
