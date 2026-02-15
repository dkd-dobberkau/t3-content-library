# Docker Production Setup Design

## Context

T3 Content Library needs containerization for production deployment at Mittwald. SSL is handled externally by Mittwald.

## Architecture

Two-container setup with Nginx reverse proxy (Ansatz A):

```
                    Port 80
                      |
                  [  nginx  ]
                  /         \
      static files      /api/* proxy
      (Vite build)          |
                      [ backend ]
                       Port 8000
                          |
                    ANTHROPIC_API_KEY
                          |
                    /app/output (Volume)
```

### Containers

- **nginx** -- serves Vite production build, proxies `/api/*` to `backend:8000`
- **backend** -- FastAPI + Uvicorn + Python library (`t3_content_library/`, `generate.py`, `config/`, `templates/`)

### Networking & Storage

- Named volume `t3-output` for generated files (mounted in backend)
- Internal Docker network `t3-network`
- Port 80 exposed on host (no SSL, handled by Mittwald)

## Dockerfiles

### backend/Dockerfile (Multi-Stage)

- **Stage 1 (builder)**: `python:3.11-slim`, installs both `requirements.txt` (root + backend) with `pip install --user`
- **Stage 2 (runtime)**: `python:3.11-slim`, non-root user (`appuser`, UID 1000), copies pip packages from builder, copies `t3_content_library/`, `config/`, `templates/`, `generate.py`, `backend/app.py`. Output directory `/app/output`. Healthcheck on `/api/health`. CMD: `uvicorn`

### frontend-vite/Dockerfile (Multi-Stage)

- **Stage 1 (builder)**: `node:20-alpine`, `npm ci`, `npm run build` produces `dist/`
- **Stage 2 (runtime)**: `nginx:alpine`, copies `dist/` to `/usr/share/nginx/html`, custom `nginx.conf`. Port 80. Healthcheck on `/`

### frontend-vite/nginx.conf

- Static files from `/usr/share/nginx/html`
- `try_files $uri $uri/ /index.html` for SPA routing
- `location /api/` proxies to `http://backend:8000`
- Gzip for JS/CSS/HTML/JSON
- Cache headers (1 year for hashed assets)

## Docker Compose

- Backend build context is repo root (`.`) with `dockerfile: backend/Dockerfile` to access all needed files
- Nginx `depends_on` backend with `condition: service_healthy`
- `.env` injected at runtime (not baked into image)
- Both containers: `restart: unless-stopped`

## File Structure (New Files)

```
t3-content-library/
├── docker-compose.yml          # NEW
├── .dockerignore               # NEW (root-level for backend build)
├── backend/
│   └── Dockerfile              # NEW
├── frontend-vite/
│   ├── Dockerfile              # NEW
│   ├── nginx.conf              # NEW
│   └── .dockerignore           # NEW
```

## Decisions

- **Nginx over FastAPI static serving**: ~10x better static file performance, handles concurrent connections efficiently
- **Two containers over single**: Standard production pattern, independently scalable
- **Multi-stage builds**: Smaller final images, no build tools in production
- **Non-root user in backend**: Security best practice
- **Build context at root for backend**: Backend Dockerfile needs files from repo root
