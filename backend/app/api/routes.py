"""REST and WebSocket routes.

Endpoint contract (docs/ARCHITECTURE.md):
  GET  /api/devices                 list device status + capabilities
  GET  /api/devices/{id}            one device status + capabilities
  POST /api/devices/{id}/command    send a single device command
  POST /api/scenes/{name}           run an orchestration routine
  GET  /api/state                   full state snapshot
  WS   /ws                          live state + progress stream
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

log = logging.getLogger("theater.api")

router = APIRouter()


class CommandBody(BaseModel):
    command: str
    params: dict[str, Any] = {}


def _manager(request: Request):
    return request.app.state.manager


def _device_payload(manager, device_id: str) -> dict[str, Any]:
    adapter = manager.get(device_id)
    if adapter is None:
        raise HTTPException(status_code=404, detail=f"unknown device {device_id!r}")
    state = manager._state.get(device_id)  # noqa: SLF001 - read-only view
    return {
        "device_id": device_id,
        "state": asdict(state) if state else None,
        "capabilities": [asdict(c) for c in adapter.capabilities()],
    }


@router.get("/api/devices")
async def list_devices(request: Request) -> dict[str, Any]:
    manager = _manager(request)
    return {
        "devices": [
            _device_payload(manager, device_id) for device_id in manager.adapters
        ]
    }


@router.get("/api/devices/{device_id}")
async def get_device(device_id: str, request: Request) -> dict[str, Any]:
    return _device_payload(_manager(request), device_id)


@router.post("/api/devices/{device_id}/command")
async def send_command(
    device_id: str, body: CommandBody, request: Request
) -> dict[str, Any]:
    manager = _manager(request)
    try:
        result = await manager.send_command(device_id, body.command, body.params)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown device {device_id!r}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NotImplementedError:
        raise HTTPException(
            status_code=501, detail=f"{device_id} does not support {body.command!r}"
        )
    except Exception as exc:  # device failure, not a client error
        log.warning("command %s on %s failed: %s", body.command, device_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))
    return {"ok": True, "result": result}


@router.post("/api/scenes/{name}")
async def run_scene(name: str, request: Request, body: dict[str, Any] | None = None) -> dict[str, Any]:
    orchestrator = request.app.state.orchestrator
    try:
        result = await orchestrator.run(name, (body or {}))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown scene {name!r}")
    return result


@router.get("/api/plex/art")
async def plex_art(request: Request, path: str, w: int = 320, h: int = 480) -> Response:
    """Proxy a Plex cover-art image so the token stays server-side."""

    adapter = request.app.state.manager.get("plex")
    if adapter is None or not hasattr(adapter, "fetch_art"):
        raise HTTPException(status_code=404, detail="plex not configured")
    try:
        data, content_type = await adapter.fetch_art(path, w, h)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"art fetch failed: {exc}")
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=120"},
    )


@router.get("/api/state")
async def get_state(request: Request) -> dict[str, Any]:
    return request.app.state.store.snapshot()


@router.get("/api/ui-config")
async def ui_config(request: Request) -> dict[str, Any]:
    """Non-secret configuration the front end needs to render controls."""

    config = request.app.state.config
    manager = request.app.state.manager
    return {
        "sources": list(config.sources.keys()),
        "default_source": config.default_source,
        "devices": list(manager.adapters.keys()),
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    bus = websocket.app.state.bus
    store = websocket.app.state.store
    # Send an initial snapshot so a freshly connected client renders immediately.
    await websocket.send_json({"type": "snapshot", "state": store.snapshot()})
    async with bus.subscribe() as queue:
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event)
        except WebSocketDisconnect:
            return
        except Exception as exc:
            log.debug("websocket closed: %s", exc)
            return
