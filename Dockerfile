# Single image serving both the FastAPI backend and the built front end.
# Two-stage: build the frontend, then run the backend which serves static assets.

# ---- Stage 1: build frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build      # outputs to /frontend/dist

# ---- Stage 2: backend runtime ----
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# Serve the built frontend from the backend (static mount).
COPY --from=frontend-build /frontend/dist ./static

# The backend reads config from /app/config (mounted read-only by compose) and
# serves the SPA from /app/static.
ENV STATIC_DIR=/app/static \
    DEVICES_CONFIG=/app/config/devices.yaml \
    APP_PORT=8487

EXPOSE 8487
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,os; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('APP_PORT','8080')+'/api/state')" || exit 1
CMD ["sh", "-c", "uvicorn app.main:app --host ${APP_BIND_HOST:-0.0.0.0} --port ${APP_PORT:-8080}"]
