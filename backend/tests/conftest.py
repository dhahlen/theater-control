"""Test configuration.

Set THEATER_SKIP_APP before any application import so that importing
``backend.app.main`` does not try to build the app from a real
``config/devices.yaml`` (which is intentionally absent in tests). Tests build
the app explicitly with an in-memory config via ``build_app``.
"""

import os

os.environ.setdefault("THEATER_SKIP_APP", "1")
