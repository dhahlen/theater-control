"""FastAPI application entrypoint (scaffold).

Wires config loading, device adapters, the in-memory state model, the REST API,
and the WebSocket. See docs/ARCHITECTURE.md for the endpoint contract. Bodies
are left for the implementing agent.
"""

from __future__ import annotations

# from fastapi import FastAPI
# app = FastAPI(title="theater-control")
#
# Expected surface (see docs/ARCHITECTURE.md):
#   GET  /api/devices
#   GET  /api/devices/{id}
#   POST /api/devices/{id}/command
#   POST /api/scenes/{name}        # e.g. theater-on, theater-off
#   GET  /api/state
#   WS   /ws
#   Static mount serving the built frontend from ./static
