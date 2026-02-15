"""
SQLite persistence for job metadata.
DB file lives alongside output files in the Docker volume.
"""

import os

import aiosqlite

OUTPUT_BASE = os.environ.get("OUTPUT_BASE", "/tmp/t3-outputs")
DB_PATH = os.path.join(OUTPUT_BASE, "t3_jobs.db")

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    page_set TEXT NOT NULL DEFAULT 'full',
    status TEXT NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    pages_done INTEGER NOT NULL DEFAULT 0,
    pages_total INTEGER NOT NULL DEFAULT 0,
    output_dir TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    duration_sec REAL NOT NULL DEFAULT 0.0
);
"""


async def init_db():
    """Create jobs table if it doesn't exist."""
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        await db.commit()


async def save_job(job_id: str, company: str, page_set: str, status: dict):
    """Upsert job metadata after completion or failure."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO jobs (
                job_id, company, page_set, status, progress,
                pages_done, pages_total, output_dir, error, created_at,
                input_tokens, output_tokens, cost_usd, duration_sec
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                status=excluded.status, progress=excluded.progress,
                pages_done=excluded.pages_done, pages_total=excluded.pages_total,
                output_dir=excluded.output_dir, error=excluded.error,
                input_tokens=excluded.input_tokens, output_tokens=excluded.output_tokens,
                cost_usd=excluded.cost_usd, duration_sec=excluded.duration_sec
            """,
            (
                job_id, company, page_set,
                status.status, status.progress,
                status.pages_done, status.pages_total,
                status.output_dir, status.error, status.created_at,
                status.input_tokens, status.output_tokens,
                status.cost_usd, status.duration_sec,
            ),
        )
        await db.commit()


async def get_job(job_id: str) -> dict | None:
    """Fetch a single job by alphacode. Returns dict or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return dict(row)


async def list_jobs(limit: int = 20) -> list[dict]:
    """Fetch recent jobs ordered by creation time."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def check_alphacode_exists(code: str) -> bool:
    """Check if an alphacode already exists in the DB."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM jobs WHERE job_id = ?", (code,)
        )
        return await cursor.fetchone() is not None
