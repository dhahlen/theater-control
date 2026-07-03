# Single image serving both the FastAPI backend and the built front end.
# Two-stage: build the frontend, then run the backend which serves static assets.

# ---- Stage 1: build frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
# RUN npm ci
COPY frontend/ ./
# RUN npm run build      # outputs to /frontend/dist

# ---- Stage 2: backend runtime ----
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# Serve the built frontend from the backend (static mount).
COPY --from=frontend-build /frontend/dist ./static
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
