# Docker Production Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Containerize the T3 Content Library (FastAPI backend + React/Vite frontend) for production deployment with Nginx reverse proxy.

**Architecture:** Two-container setup -- Nginx serves static Vite build and proxies `/api/*` to FastAPI backend. Named volume for generated output. No SSL (handled externally by Mittwald).

**Tech Stack:** Docker, docker-compose, Nginx, Python 3.11, Node 20, FastAPI, Vite/React

---

### Task 1: Root .dockerignore

**Files:**
- Create: `.dockerignore`

**Step 1: Create .dockerignore**

This file applies when docker-compose builds the backend with `context: .`

```dockerignore
.git/
.venv/
__pycache__/
*.pyc
output/
.env
.pytest_cache/
.DS_Store
node_modules/
frontend-vite/node_modules/
frontend/
docs/
tests/
*.png
.claude/
.playwright-mcp/
.codegraph/
```

**Step 2: Commit**

```bash
git add .dockerignore
git commit -m "chore: add root .dockerignore for backend build context"
```

---

### Task 2: Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`

**Step 1: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements-root.txt
COPY backend/requirements.txt ./requirements-backend.txt
RUN pip install --no-cache-dir --user -r requirements-root.txt -r requirements-backend.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local

COPY --chown=appuser:appuser t3_content_library/ ./t3_content_library/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser generate.py ./
COPY --chown=appuser:appuser backend/app.py ./backend/

RUN mkdir -p /app/output && chown appuser:appuser /app/output

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV T3_LIB_PATH=/app
ENV OUTPUT_BASE=/app/output

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Verify Dockerfile syntax**

Run: `docker build --check -f backend/Dockerfile .` (or just review manually -- no test needed yet)

**Step 3: Commit**

```bash
git add backend/Dockerfile
git commit -m "feat: add backend Dockerfile with multi-stage build"
```

---

### Task 3: Frontend .dockerignore

**Files:**
- Create: `frontend-vite/.dockerignore`

**Step 1: Create frontend-vite/.dockerignore**

```dockerignore
node_modules/
dist/
.DS_Store
```

**Step 2: Commit**

```bash
git add frontend-vite/.dockerignore
git commit -m "chore: add frontend .dockerignore"
```

---

### Task 4: Nginx Configuration

**Files:**
- Create: `frontend-vite/nginx.conf`

**Step 1: Create frontend-vite/nginx.conf**

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 256;
    gzip_vary on;

    # Cache hashed assets (Vite adds content hash to filenames)
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support (for /api/jobs/{id}/events)
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Step 2: Commit**

```bash
git add frontend-vite/nginx.conf
git commit -m "feat: add nginx config with API proxy and SPA routing"
```

---

### Task 5: Frontend Dockerfile

**Files:**
- Create: `frontend-vite/Dockerfile`

**Step 1: Create frontend-vite/Dockerfile**

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.js ./
COPY src/ ./src/
RUN npm run build

FROM nginx:alpine

RUN apk add --no-cache curl

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**Step 2: Commit**

```bash
git add frontend-vite/Dockerfile
git commit -m "feat: add frontend Dockerfile with Vite build and Nginx"
```

---

### Task 6: Docker Compose

**Files:**
- Create: `docker-compose.yml`

**Step 1: Create docker-compose.yml**

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: t3-backend
    env_file:
      - .env
    environment:
      - T3_LIB_PATH=/app
      - OUTPUT_BASE=/app/output
    volumes:
      - t3-output:/app/output
    networks:
      - t3-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    build:
      context: ./frontend-vite
      dockerfile: Dockerfile
    container_name: t3-nginx
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - t3-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  t3-output:

networks:
  t3-network:
    driver: bridge
```

**Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose with backend and nginx services"
```

---

### Task 7: Build and Smoke Test

**Step 1: Build both images**

Run: `docker compose build`
Expected: Both images build successfully without errors.

**Step 2: Start the stack**

Run: `docker compose up -d`
Expected: Both containers start. Backend becomes healthy first, then nginx starts.

**Step 3: Verify backend health**

Run: `docker compose exec backend curl -f http://localhost:8000/api/health`
Expected: `{"status":"ok","t3_lib_path":"/app"}`

**Step 4: Verify nginx serves frontend**

Run: `curl -s http://localhost/ | head -5`
Expected: HTML containing `<div id="root">` and `T3 Content Library`

**Step 5: Verify API proxy works**

Run: `curl -s http://localhost/api/health`
Expected: `{"status":"ok","t3_lib_path":"/app"}`

**Step 6: Stop the stack**

Run: `docker compose down`

**Step 7: Commit (if any fixes were needed)**

Only if adjustments were made during smoke test.
