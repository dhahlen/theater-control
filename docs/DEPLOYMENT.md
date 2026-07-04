# Deployment

The whole stack is one Docker image: a multi-stage build compiles the React
front end and the runtime image serves it from the FastAPI backend. You can
either build that image on the theater host or pull a prebuilt one from the
GitHub Container Registry (GHCR).

## Networking and port

The container runs with `network_mode: host` because the Trinnov and MadVR Envy
accept control only from the same subnet and MadVR power-on uses a Wake-on-LAN
broadcast. With host networking the service binds `APP_PORT` directly on the
host, so that port must be free. The default is `8487` (chosen to avoid the
common `8080` and the ports already used by the existing stack). Change it in
`.env` if needed.

## Files the host needs

Only three files are required on the theater host, in one directory:

```
theater-control/
  docker-compose.yml     # from this repo
  .env                   # secrets; copy from .env.example, fill in
  config/devices.yaml    # device details; copy from config/devices.example.yaml
```

Neither `.env` nor `config/devices.yaml` is committed. When pulling a prebuilt
image you do not need the source tree at all, just these three files.

## Option A: build from source on the host

```
git clone https://github.com/dhahlen/theater-control.git
cd theater-control
cp .env.example .env                          # then edit
cp config/devices.example.yaml config/devices.yaml   # then edit
docker compose up -d --build
```

Update later with:

```
git pull
docker compose up -d --build
```

## Option B: pull a prebuilt image from GHCR

The `Publish container image` GitHub Action builds and pushes
`ghcr.io/dhahlen/theater-control` on every push to `main` and on version tags
(`v1.2.3`). `docker-compose.yml` already points `image:` at that registry, so on
the host you only keep `docker-compose.yml`, `.env`, and `config/devices.yaml`:

```
# remove or comment the `build:` block in docker-compose.yml so compose pulls
docker compose pull
docker compose up -d
```

Update later with:

```
docker compose pull
docker compose up -d
```

If the GHCR package is private, authenticate first with a GitHub personal access
token that has `read:packages`:

```
echo <TOKEN> | docker login ghcr.io -u <github-username> --password-stdin
```

## Versioning

The project uses semantic versioning. To cut a release and publish a pinned
image tag:

```
git tag v0.2.0
git push origin v0.2.0
```

The Action then publishes `ghcr.io/dhahlen/theater-control:0.2.0`,
`:0.2`, and `:latest`. Pin a specific version on the host by setting, for
example, `image: ghcr.io/dhahlen/theater-control:0.2.0` in `docker-compose.yml`,
which makes rollbacks a one-line change.

## Verifying a running deployment

```
docker compose ps                 # container up, health: healthy
curl http://<host-ip>:8487/api/state
```

Open `http://<host-ip>:8487` on the iPad in Safari (landscape) and add it to the
Home Screen for a fullscreen, chrome-free experience. The backend health check
polls `/api/state`; a device that is offline degrades that panel only, never the
whole interface.
