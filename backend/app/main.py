"""FastAPI application entrypoint.

Wires config loading, device adapters, the in-memory state model, the REST API,
and the WebSocket, and serves the built front end. See docs/ARCHITECTURE.md for
the endpoint contract.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core.config import AppConfig, ConfigError, load_config
from .core.events import EventBus
from .core.manager import DeviceManager
from .core.state import StateStore
from .orchestration.registry import Orchestrator

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("theater")

# Directory holding the built front end (mounted at /). Overridable for tests.
STATIC_DIR = Path(os.environ.get("STATIC_DIR", "backend/app/static"))


def build_app(config: AppConfig | None = None) -> FastAPI:
    if config is None:
        config = load_config()

    store = StateStore()
    bus = EventBus()
    manager = DeviceManager(config, store, bus)
    orchestrator = Orchestrator(config, manager, bus)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log.info(
            "starting theater-control with %d device(s): %s",
            len(manager.adapters),
            ", ".join(manager.adapters) or "none",
        )
        await manager.start()
        try:
            yield
        finally:
            await manager.stop()

    app = FastAPI(title="theater-control", lifespan=lifespan)
    app.state.config = config
    app.state.store = store
    app.state.bus = bus
    app.state.manager = manager
    app.state.orchestrator = orchestrator

    app.include_router(router)

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    else:
        log.info("static dir %s not present; front end not mounted", STATIC_DIR)

    return app


def _create_app() -> FastAPI:
    try:
        return build_app()
    except ConfigError as exc:
        log.error("configuration error: %s", exc)
        raise SystemExit(1) from exc


# Uvicorn entrypoint: `uvicorn backend.app.main:app`.
app = _create_app() if os.environ.get("THEATER_SKIP_APP") != "1" else None
