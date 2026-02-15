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
