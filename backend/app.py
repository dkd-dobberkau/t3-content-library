"""
FastAPI backend for T3 Content Library.
Wraps the existing Python CLI and provides REST API + SSE for progress updates.
"""

import asyncio
import json
import os
import sys
import uuid
import zipfile
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="T3 Content Library API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs: dict = {}

# Path to the t3-content-library repo root (backend/ is inside the repo)
T3_LIB_PATH = os.environ.get("T3_LIB_PATH", os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_BASE = os.environ.get("OUTPUT_BASE", "/tmp/t3-outputs")


class GenerateRequest(BaseModel):
    company: str


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    current_page: str | None = None
    pages_done: int = 0
    pages_total: int = 20
    output_dir: str | None = None
    error: str | None = None
    created_at: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_sec: float = 0.0


@app.post("/api/generate", response_model=JobStatus)
async def start_generation(req: GenerateRequest):
    """Start a new content generation job."""
    job_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(OUTPUT_BASE, job_id)
    os.makedirs(output_dir, exist_ok=True)

    job = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        output_dir=output_dir,
        created_at=datetime.now().isoformat(),
    )
    jobs[job_id] = {
        "status": job,
        "company": req.company,
        "events": [],
    }

    # Start background task
    asyncio.create_task(_run_generation(job_id, req.company, output_dir))

    return job


async def _run_generation(job_id: str, company: str, output_dir: str):
    """Run the generation process in background."""
    job_data = jobs[job_id]
    job_data["status"].status = "running"

    try:
        # Call the CLI with --jsonl for structured output
        process = await asyncio.create_subprocess_exec(
            sys.executable, "generate.py",
            "--company", company,
            "--output-dir", output_dir,
            "--jsonl",
            cwd=T3_LIB_PATH,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded = line.decode().strip()
            if not decoded:
                continue

            try:
                evt = json.loads(decoded)
            except json.JSONDecodeError:
                job_data["events"].append(decoded)
                continue

            job_data["events"].append(decoded)
            status = job_data["status"]

            if evt.get("event") == "page_done":
                status.pages_done = evt["done"]
                status.progress = int(evt["done"] / evt["total"] * 100)
                status.current_page = evt["title"]
                status.input_tokens += evt.get("input_tokens", 0)
                status.output_tokens += evt.get("output_tokens", 0)
            elif evt.get("event") == "complete":
                status.input_tokens = evt.get("total_input_tokens", status.input_tokens)
                status.output_tokens = evt.get("total_output_tokens", status.output_tokens)
                status.cost_usd = evt.get("cost_usd", 0.0)
                status.duration_sec = evt.get("duration_sec", 0.0)

        await process.wait()

        if process.returncode == 0:
            job_data["status"].status = "completed"
            job_data["status"].progress = 100
            job_data["status"].pages_done = 20
        else:
            stderr = await process.stderr.read()
            job_data["status"].status = "failed"
            job_data["status"].error = stderr.decode()[:2000]

    except Exception as e:
        job_data["status"].status = "failed"
        job_data["status"].error = str(e)


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get current job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]["status"]


@app.get("/api/jobs/{job_id}/events")
async def stream_events(job_id: str):
    """SSE endpoint for real-time progress updates."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        last_idx = 0
        while True:
            job_data = jobs.get(job_id)
            if not job_data:
                break

            status = job_data["status"]
            events = job_data["events"]

            # Send new events
            if len(events) > last_idx:
                for evt_raw in events[last_idx:]:
                    try:
                        evt = json.loads(evt_raw)
                        yield f"data: {json.dumps({'type': 'log', 'event': evt})}\n\n"
                    except json.JSONDecodeError:
                        yield f"data: {json.dumps({'type': 'log', 'message': evt_raw})}\n\n"
                last_idx = len(events)

            # Send status update
            yield f"data: {json.dumps({'type': 'status', 'status': status.status, 'progress': status.progress, 'pages_done': status.pages_done, 'current_page': status.current_page, 'input_tokens': status.input_tokens, 'output_tokens': status.output_tokens, 'cost_usd': status.cost_usd})}\n\n"

            if status.status in ("completed", "failed"):
                yield f"data: {json.dumps({'type': 'done', 'status': status.status, 'error': status.error, 'input_tokens': status.input_tokens, 'output_tokens': status.output_tokens, 'cost_usd': status.cost_usd, 'duration_sec': status.duration_sec})}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/jobs/{job_id}/pages")
async def list_pages(job_id: str):
    """List all generated pages for a job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    output_dir = jobs[job_id]["status"].output_dir
    if not output_dir or not os.path.exists(output_dir):
        return {"pages": []}

    pages = []
    for root, dirs, files in os.walk(output_dir):
        for f in sorted(files):
            if f.endswith(".md"):
                filepath = os.path.join(root, f)
                rel_path = os.path.relpath(filepath, output_dir)
                with open(filepath, "r", encoding="utf-8") as fh:
                    content = fh.read()

                # Parse YAML frontmatter
                meta = {}
                body = content
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        import yaml
                        try:
                            meta = yaml.safe_load(parts[1]) or {}
                        except Exception:
                            pass
                        body = parts[2].strip()

                pages.append({
                    "filename": f,
                    "path": rel_path,
                    "title": meta.get("title", f.replace(".md", "").replace("-", " ").title()),
                    "slug": meta.get("slug", ""),
                    "layout": meta.get("layout", ""),
                    "meta": meta,
                    "content": body,
                    "raw": content,
                })

    return {"pages": pages}


@app.get("/api/jobs/{job_id}/download")
async def download_zip(job_id: str):
    """Download all generated files as ZIP."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    output_dir = jobs[job_id]["status"].output_dir
    if not output_dir or not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="No output files found")

    company = jobs[job_id]["company"]
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in company).strip().replace(" ", "-")

    zip_path = f"/tmp/t3-{safe_name}-{job_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                filepath = os.path.join(root, f)
                arcname = os.path.relpath(filepath, output_dir)
                zf.write(filepath, arcname)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"t3-content-{safe_name}.zip",
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "t3_lib_path": T3_LIB_PATH}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
